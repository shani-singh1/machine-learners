from __future__ import annotations

from pathlib import Path

import pandas as pd


FEATURE_COLUMNS = [
    "sar_water_persistence",
    "rainfall_accumulation",
    "low_lying_score",
    "impervious_change_rate",
    "population_exposure",
]


class FeatureBuilder:
    def __init__(self, project_root: Path, city: str) -> None:
        self.project_root = project_root
        self.city = city
        self.processed_root = project_root / "data" / "processed" / city
        self.features_root = project_root / "data" / "features"

    def run(self) -> Path:
        input_files = sorted(self.processed_root.glob("*.parquet"))
        if not input_files:
            raise RuntimeError(f"No processed parquet files found in {self.processed_root}")

        frames = [pd.read_parquet(path) for path in input_files]
        dataset = pd.concat(frames, ignore_index=True)
        dataset = dataset.sort_values(["tile_id", "year", "month"]).reset_index(drop=True)
        dataset["time_window"] = dataset["year_month"]
        dataset["imagery_reference"] = dataset["year_month"].map(
            lambda ym: f"data/raw/sentinel_1/{ym[:4]}/{ym[5:7]}/manifest.json"
        )

        # Keep a transparent proxy vulnerability target for baseline training.
        dataset["target_vulnerability_proxy"] = (
            0.35 * dataset["rainfall_accumulation"] / (dataset["rainfall_accumulation"].max() + 1e-9)
            + 0.25 * dataset["sar_water_persistence"]
            + 0.20 * dataset["low_lying_score"]
            + 0.10 * dataset["impervious_change_rate"] / (dataset["impervious_change_rate"].max() + 1e-9)
            + 0.10 * dataset["population_exposure"]
        )

        self.features_root.mkdir(parents=True, exist_ok=True)
        out_path = self.features_root / "flood_dataset.parquet"
        dataset.to_parquet(out_path, index=False)
        return out_path
