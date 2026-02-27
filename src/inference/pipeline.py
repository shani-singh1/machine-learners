from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.features.dataset_builder import FEATURE_COLUMNS
from src.models.temporal import TemporalTrainer


class InferencePipeline:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.dataset_path = project_root / "data" / "features" / "flood_dataset.parquet"
        self.model_path = project_root / "data" / "results" / "models" / "temporal_model.joblib"
        self.results_path = project_root / "data" / "results" / "vulnerability_scores.parquet"

    def run(self) -> Path:
        if not self.dataset_path.exists():
            raise RuntimeError(f"Dataset not found: {self.dataset_path}")
        if not self.model_path.exists():
            raise RuntimeError(f"Trained model not found: {self.model_path}")

        dataset = pd.read_parquet(self.dataset_path)
        inference_frame = TemporalTrainer.make_inference_frame(dataset)
        temporal_features = (
            FEATURE_COLUMNS
            + [f"{c}_lag1" for c in FEATURE_COLUMNS]
            + [f"{c}_lag2" for c in FEATURE_COLUMNS]
            + [f"{c}_lag3" for c in FEATURE_COLUMNS]
            + [f"{c}_roll3" for c in FEATURE_COLUMNS]
        )

        model = joblib.load(self.model_path)
        raw_scores = model.predict(inference_frame[temporal_features])
        min_val = float(np.min(raw_scores))
        max_val = float(np.max(raw_scores))
        norm_scores = (raw_scores - min_val) / (max_val - min_val + 1e-9)

        output = inference_frame[["tile_id", "year", "month", "year_month", "lon", "lat"]].copy()
        output["vulnerability_score"] = norm_scores
        output["vulnerability_rank"] = output["vulnerability_score"].rank(method="average", ascending=False)

        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        output.to_parquet(self.results_path, index=False)
        return self.results_path
