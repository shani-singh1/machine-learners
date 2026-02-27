from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
SCORES_PATH = RESULTS_DIR / "vulnerability_scores.parquet"
EVAL_PATH = RESULTS_DIR / "evaluation.json"
TRAINING_PATH = RESULTS_DIR / "training_metrics.json"

app = FastAPI(title="Urban Flood Vulnerability API", version="0.1.0")


def _load_scores() -> pd.DataFrame:
    if not SCORES_PATH.exists():
        raise HTTPException(status_code=404, detail="vulnerability_scores.parquet not found")
    return pd.read_parquet(SCORES_PATH)


@app.get("/vulnerability/latest")
def vulnerability_latest(limit: int = Query(default=200, ge=1, le=10000)) -> dict[str, Any]:
    df = _load_scores()
    latest_month = df["year_month"].max()
    latest = df.loc[df["year_month"] == latest_month].copy()
    latest = latest.sort_values("vulnerability_score", ascending=False).head(limit)
    return {"year_month": latest_month, "count": int(latest.shape[0]), "rows": latest.to_dict(orient="records")}


@app.get("/vulnerability/by_zone")
def vulnerability_by_zone(
    year_month: str | None = None,
    bins_lat: int = Query(default=8, ge=2, le=100),
    bins_lon: int = Query(default=8, ge=2, le=100),
) -> dict[str, Any]:
    df = _load_scores().copy()
    if year_month:
        df = df.loc[df["year_month"] == year_month]
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No rows found for year_month={year_month}")
    else:
        latest_month = df["year_month"].max()
        df = df.loc[df["year_month"] == latest_month]

    df["zone_lat"] = pd.cut(df["lat"], bins=bins_lat, labels=False)
    df["zone_lon"] = pd.cut(df["lon"], bins=bins_lon, labels=False)
    grouped = (
        df.groupby(["zone_lat", "zone_lon"], as_index=False)["vulnerability_score"]
        .mean()
        .sort_values("vulnerability_score", ascending=False)
    )
    grouped["zone_id"] = grouped.apply(lambda r: f"z_{int(r.zone_lat)}_{int(r.zone_lon)}", axis=1)
    return {"count": int(grouped.shape[0]), "rows": grouped.to_dict(orient="records")}


@app.get("/metadata")
def metadata() -> dict[str, Any]:
    df = _load_scores()
    payload: dict[str, Any] = {
        "rows": int(df.shape[0]),
        "months": sorted(df["year_month"].unique().tolist()),
        "sources": ["sentinel_1", "sentinel_2", "era5", "dem", "ghsl", "worldpop", "osm_roads"],
    }
    if EVAL_PATH.exists():
        payload["evaluation"] = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    if TRAINING_PATH.exists():
        payload["training_metrics"] = json.loads(TRAINING_PATH.read_text(encoding="utf-8"))
    return payload


@app.get("/vulnerability/timeseries")
def vulnerability_timeseries() -> dict[str, Any]:
    df = _load_scores().copy()
    grouped = (
        df.groupby("year_month", as_index=False)["vulnerability_score"]
        .mean()
        .sort_values("year_month")
        .reset_index(drop=True)
    )
    return {"count": int(grouped.shape[0]), "rows": grouped.to_dict(orient="records")}
