from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from src.models.temporal import TemporalTrainer


class TrainingPipeline:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.dataset_path = project_root / "data" / "features" / "flood_dataset.parquet"
        self.models_root = project_root / "data" / "results" / "models"
        self.results_root = project_root / "data" / "results"

    def run(self) -> dict:
        if not self.dataset_path.exists():
            raise RuntimeError(f"Dataset not found: {self.dataset_path}")

        dataset = pd.read_parquet(self.dataset_path)
        trainer = TemporalTrainer()
        artifacts = trainer.fit(dataset)

        self.models_root.mkdir(parents=True, exist_ok=True)
        self.results_root.mkdir(parents=True, exist_ok=True)

        baseline_path = self.models_root / "baseline_model.joblib"
        temporal_path = self.models_root / "temporal_model.joblib"
        joblib.dump(artifacts.baseline_model, baseline_path)
        joblib.dump(artifacts.temporal_model, temporal_path)

        metrics = {
            "baseline": artifacts.baseline_metrics,
            "temporal": artifacts.temporal_metrics,
            "selected_temporal_model_name": artifacts.selected_temporal_model_name,
            "selected_temporal_config": artifacts.selected_temporal_config,
            "split_info": artifacts.split_info,
            "top_feature_importance": artifacts.feature_importance[:20],
            "model_paths": {
                "baseline": str(baseline_path),
                "temporal": str(temporal_path),
            },
        }
        (self.results_root / "training_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        (self.results_root / "feature_importance.json").write_text(
            json.dumps(artifacts.feature_importance, indent=2), encoding="utf-8"
        )
        return metrics
