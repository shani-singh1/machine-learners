from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _event_intensity(month: int) -> float:
    return 1.0 if month in {8, 9, 10} else 0.35 if month in {6, 7, 11} else 0.1


class EvaluationPipeline:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.scores_path = project_root / "data" / "results" / "vulnerability_scores.parquet"
        self.output_path = project_root / "data" / "results" / "evaluation.json"

    def run(self) -> dict:
        if not self.scores_path.exists():
            raise RuntimeError(f"Scores not found: {self.scores_path}")

        scores = pd.read_parquet(self.scores_path)
        monthly = (
            scores.groupby("year_month", as_index=False)["vulnerability_score"]
            .mean()
            .sort_values("year_month")
            .reset_index(drop=True)
        )
        monthly["month"] = monthly["year_month"].str[-2:].astype(int)
        monthly["historical_event_proxy"] = monthly["month"].map(_event_intensity)

        rank_corr = float(
            monthly["vulnerability_score"].corr(monthly["historical_event_proxy"], method="spearman")
        )

        q80 = scores["vulnerability_score"].quantile(0.8)
        q20 = scores["vulnerability_score"].quantile(0.2)
        high_mean = float(scores.loc[scores["vulnerability_score"] >= q80, "vulnerability_score"].mean())
        low_mean = float(scores.loc[scores["vulnerability_score"] <= q20, "vulnerability_score"].mean())

        metrics = {
            "rank_correlation_spearman": rank_corr,
            "high_vs_low_vulnerability_gap": high_mean - low_mean,
            "high_vulnerability_mean": high_mean,
            "low_vulnerability_mean": low_mean,
            "months_evaluated": int(monthly.shape[0]),
        }

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return metrics
