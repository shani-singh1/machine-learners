from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score

from src.features.dataset_builder import FEATURE_COLUMNS


def _add_temporal_lags_and_target(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame = frame.sort_values(["tile_id", "year", "month"]).reset_index(drop=True)

    for col in FEATURE_COLUMNS:
        frame[f"{col}_lag1"] = frame.groupby("tile_id")[col].shift(1)
        frame[f"{col}_lag2"] = frame.groupby("tile_id")[col].shift(2)
        frame[f"{col}_lag3"] = frame.groupby("tile_id")[col].shift(3)
        frame[f"{col}_roll3"] = (
            frame.groupby("tile_id")[col].rolling(window=3, min_periods=3).mean().reset_index(level=0, drop=True)
        )

    # Production-safe target: predict next month's vulnerability proxy.
    frame["target_next_month"] = frame.groupby("tile_id")["target_vulnerability_proxy"].shift(-1)
    frame["time_id"] = frame["year"] * 100 + frame["month"]
    return frame.dropna().reset_index(drop=True)


def _build_splits(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    unique_time = sorted(frame["time_id"].unique().tolist())
    if len(unique_time) < 24:
        raise RuntimeError("Not enough months to create train/validation/test chronological split.")

    test_time = set(unique_time[-12:])
    val_time = set(unique_time[-24:-12])
    train_time = set(unique_time[:-24])

    train_df = frame.loc[frame["time_id"].isin(train_time)].copy()
    val_df = frame.loc[frame["time_id"].isin(val_time)].copy()
    test_df = frame.loc[frame["time_id"].isin(test_time)].copy()

    if train_df.empty or val_df.empty or test_df.empty:
        raise RuntimeError("Chronological split produced empty train/val/test partitions.")
    return train_df, val_df, test_df


def _metrics(y_true: pd.Series, y_pred: pd.Series | Any) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


@dataclass(frozen=True)
class TrainArtifacts:
    baseline_model: Ridge
    temporal_model: Any
    baseline_metrics: dict[str, float]
    temporal_metrics: dict[str, float]
    selected_temporal_model_name: str
    selected_temporal_config: dict[str, Any]
    split_info: dict[str, str]
    feature_importance: list[dict[str, float]]


class TemporalTrainer:
    def fit(self, dataset: pd.DataFrame) -> TrainArtifacts:
        labeled = _add_temporal_lags_and_target(dataset)
        train_df, val_df, test_df = _build_splits(labeled)
        target = "target_next_month"

        lag_cols = (
            [f"{c}_lag1" for c in FEATURE_COLUMNS]
            + [f"{c}_lag2" for c in FEATURE_COLUMNS]
            + [f"{c}_lag3" for c in FEATURE_COLUMNS]
            + [f"{c}_roll3" for c in FEATURE_COLUMNS]
        )

        baseline_features = FEATURE_COLUMNS
        temporal_features = FEATURE_COLUMNS + lag_cols

        bx_train_val = pd.concat([train_df[baseline_features], val_df[baseline_features]], axis=0)
        by_train_val = pd.concat([train_df[target], val_df[target]], axis=0)
        bx_test = test_df[baseline_features]
        by_test = test_df[target]

        baseline_model = Ridge(alpha=1.0, random_state=42)
        baseline_model.fit(bx_train_val, by_train_val)
        baseline_pred = baseline_model.predict(bx_test)

        candidates = {
            "random_forest": [
                RandomForestRegressor(
                    n_estimators=400,
                    max_depth=None,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                ),
                RandomForestRegressor(
                    n_estimators=700,
                    max_depth=20,
                    min_samples_leaf=1,
                    random_state=42,
                    n_jobs=-1,
                ),
            ],
            "extra_trees": [
                ExtraTreesRegressor(
                    n_estimators=600,
                    max_depth=None,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                ),
                ExtraTreesRegressor(
                    n_estimators=900,
                    max_depth=24,
                    min_samples_leaf=1,
                    random_state=42,
                    n_jobs=-1,
                ),
            ],
            "hist_gbrt": [
                HistGradientBoostingRegressor(
                    max_depth=8,
                    learning_rate=0.05,
                    max_iter=500,
                    random_state=42,
                ),
                HistGradientBoostingRegressor(
                    max_depth=12,
                    learning_rate=0.03,
                    max_iter=900,
                    random_state=42,
                ),
            ],
        }

        x_train = train_df[temporal_features]
        y_train = train_df[target]
        x_val = val_df[temporal_features]
        y_val = val_df[target]

        best_name = ""
        best_model: Any | None = None
        best_config: dict[str, Any] = {}
        best_val_mae = float("inf")

        for name, model_variants in candidates.items():
            for model in model_variants:
                candidate = clone(model)
                candidate.fit(x_train, y_train)
                val_pred = candidate.predict(x_val)
                val_mae = mean_absolute_error(y_val, val_pred)
                if val_mae < best_val_mae:
                    best_val_mae = float(val_mae)
                    best_name = name
                    best_model = candidate
                    best_config = candidate.get_params()

        assert best_model is not None

        temporal_model = clone(best_model)
        x_train_val = pd.concat([train_df[temporal_features], val_df[temporal_features]], axis=0)
        y_train_val = pd.concat([train_df[target], val_df[target]], axis=0)
        temporal_model.fit(x_train_val, y_train_val)
        temporal_pred = temporal_model.predict(test_df[temporal_features])

        baseline_metrics = _metrics(by_test, baseline_pred)
        temporal_metrics = _metrics(test_df[target], temporal_pred)
        temporal_metrics["validation_mae_for_selected_model"] = best_val_mae
        temporal_metrics["mae_improvement_over_baseline"] = baseline_metrics["mae"] - temporal_metrics["mae"]
        temporal_metrics["r2_improvement_over_baseline"] = temporal_metrics["r2"] - baseline_metrics["r2"]

        if hasattr(temporal_model, "feature_importances_"):
            importances = temporal_model.feature_importances_
            feature_importance = [
                {"feature": feature, "importance": float(importance)}
                for feature, importance in sorted(
                    zip(temporal_features, importances, strict=False),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ]
        else:
            feature_importance = []

        return TrainArtifacts(
            baseline_model=baseline_model,
            temporal_model=temporal_model,
            baseline_metrics=baseline_metrics,
            temporal_metrics=temporal_metrics,
            selected_temporal_model_name=best_name,
            selected_temporal_config=best_config,
            split_info={
                "train_end": str(max(train_df["time_id"])),
                "val_start": str(min(val_df["time_id"])),
                "val_end": str(max(val_df["time_id"])),
                "test_start": str(min(test_df["time_id"])),
                "test_end": str(max(test_df["time_id"])),
            },
            feature_importance=feature_importance,
        )

    @staticmethod
    def make_inference_frame(dataset: pd.DataFrame) -> pd.DataFrame:
        frame = _add_temporal_lags_and_target(dataset)
        return frame.drop(columns=["target_next_month"], errors="ignore")
