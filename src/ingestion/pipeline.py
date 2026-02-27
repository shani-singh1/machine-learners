from __future__ import annotations

import json
from datetime import datetime
from time import perf_counter
from typing import Any
from shutil import copy2

from src.common.settings import AppSettings
from src.common.time_utils import iter_month_windows
from src.ingestion.adapters import (
    build_manifest,
    fetch_dem_points,
    fetch_era5_equivalent_timeseries,
    fetch_osm_roads,
    fetch_sentinel1_monthly_preprocessed,
    fetch_sentinel2_monthly_preprocessed,
    write_era5_month_from_timeseries,
    write_ghsl_reference,
    write_worldpop_reference,
)
from src.ingestion.cdse_client import CDSEClient
from src.ingestion.config import IngestionConfig


class IngestionPipeline:
    def __init__(self, settings: AppSettings, config: IngestionConfig, live_fetch: bool = False) -> None:
        self.settings = settings
        self.config = config
        self.raw_root = settings.project_root / "data" / "raw"
        self.cdse = CDSEClient(settings=settings)
        self.live_fetch = live_fetch

    def run(self) -> None:
        self._log("Starting ingestion run.")
        for source_name, enabled in self.config.sources.items():
            if not enabled:
                self._log(f"Skipping disabled source: {source_name}")
                continue
            self._run_source(source_name)
        self._log("Ingestion run finished.")

    @staticmethod
    def _log(message: str) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] {message}", flush=True)

    def _run_source(self, source_name: str) -> None:
        self._log(f"Source start: {source_name}")
        source_started = perf_counter()
        completed = 0
        skipped = 0
        errors = 0
        static_payload_cache: dict[str, Any] | None = None
        for window in iter_month_windows(self.config.date_range.start, self.config.date_range.end):
            label = f"{source_name} {window.year:04d}-{window.month:02d}"
            self._log(f"Month start: {label}")
            out_dir = self.raw_root / source_name / str(window.year) / f"{window.month:02d}"
            out_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = out_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    existing = json.loads(manifest_path.read_text(encoding="utf-8"))
                    if existing.get("payload", {}).get("status") == "downloaded":
                        skipped += 1
                        self._log(f"Month skip (already downloaded): {label}")
                        continue
                except Exception:
                    pass

            month_started = perf_counter()
            if source_name in {"sentinel_1", "sentinel_2"}:
                try:
                    if source_name == "sentinel_1":
                        payload = fetch_sentinel1_monthly_preprocessed(
                            self.cdse, self.config.roi.bbox_wgs84, window, out_dir
                        )
                    else:
                        payload = fetch_sentinel2_monthly_preprocessed(
                            self.cdse, self.config.roi.bbox_wgs84, window, out_dir
                        )
                except Exception as exc:
                    payload = {
                        "status": "api_error",
                        "source": source_name,
                        "error": str(exc),
                        "window_start": window.start_date.isoformat(),
                        "window_end": window.end_date.isoformat(),
                    }
            elif source_name == "era5":
                try:
                    if static_payload_cache is None:
                        static_payload_cache = fetch_era5_equivalent_timeseries(
                            self.config.roi.bbox_wgs84,
                            self.config.date_range.start,
                            self.config.date_range.end,
                        )
                    payload = write_era5_month_from_timeseries(static_payload_cache, window, out_dir)
                except Exception as exc:
                    payload = {"status": "api_error", "source": source_name, "error": str(exc)}
            elif source_name == "dem":
                try:
                    if static_payload_cache is None:
                        static_payload_cache = fetch_dem_points(self.config.roi.bbox_wgs84, out_dir)
                    else:
                        first_dir = self.raw_root / source_name / str(self.config.date_range.start.year) / "01"
                        for tif in first_dir.glob("*.tif"):
                            copy2(tif, out_dir / tif.name)
                    payload = {"status": "downloaded", "files": [p.name for p in out_dir.glob("*.tif")]}
                except Exception as exc:
                    payload = {"status": "api_error", "source": source_name, "error": str(exc)}
            elif source_name == "osm_roads":
                try:
                    if static_payload_cache is None:
                        static_payload_cache = fetch_osm_roads(self.config.roi.bbox_wgs84, out_dir)
                    else:
                        (out_dir / "roads_overpass.json").write_text(
                            json.dumps(
                                {
                                    "status": "reused_static_roads",
                                    "note": "Road graph does not change significantly month-to-month.",
                                },
                                indent=2,
                            ),
                            encoding="utf-8",
                        )
                    payload = {"status": "downloaded", "file": "roads_overpass.json"}
                except Exception as exc:
                    payload = {"status": "api_error", "source": source_name, "error": str(exc)}
            elif source_name == "worldpop":
                try:
                    if static_payload_cache is None:
                        static_payload_cache = write_worldpop_reference(window, out_dir)
                    else:
                        (out_dir / "worldpop_reuse.json").write_text(
                            json.dumps(
                                {
                                    "status": "reused_static_worldpop",
                                    "reference": f"data/raw/{source_name}/{self.config.date_range.start.year}/01/worldpop_metadata.json",
                                },
                                indent=2,
                            ),
                            encoding="utf-8",
                        )
                    payload = {"status": "downloaded", "file": "worldpop_metadata.json"}
                except Exception as exc:
                    payload = {"status": "api_error", "source": source_name, "error": str(exc)}
            elif source_name == "ghsl":
                try:
                    if static_payload_cache is None:
                        static_payload_cache = write_ghsl_reference(window, out_dir)
                    else:
                        (out_dir / "ghsl_reuse.json").write_text(
                            json.dumps(
                                {
                                    "status": "reused_static_ghsl",
                                    "reference": (
                                        "data/raw/ghsl/"
                                        f"{self.config.date_range.start.year}/01/"
                                        "GHS_BUILT_S_E2020_GLOBE_R2023A_4326_30ss_V1_0.zip"
                                    ),
                                },
                                indent=2,
                            ),
                            encoding="utf-8",
                        )
                    payload = {"status": "downloaded", "file": "GHS_BUILT_S_E2020_GLOBE_R2023A_4326_30ss_V1_0.zip"}
                except Exception as exc:
                    payload = {"status": "api_error", "source": source_name, "error": str(exc)}
            else:
                payload = {
                    "status": "planned_source",
                    "source": source_name,
                    "window_start": window.start_date.isoformat(),
                    "window_end": window.end_date.isoformat(),
                }

            manifest = build_manifest(
                city=self.config.city,
                country=self.config.country,
                source_name=source_name,
                window=window,
                roi_name=self.config.roi.name,
                bbox_wgs84=self.config.roi.bbox_wgs84,
                payload=payload,
            )
            manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
            elapsed = perf_counter() - month_started
            status = payload.get("status", "unknown")
            if status == "downloaded":
                completed += 1
            elif status == "api_error":
                errors += 1
            details = ""
            if "bytes" in payload:
                details = f", bytes={payload['bytes']}"
            elif "file" in payload:
                details = f", file={payload['file']}"
            elif "files" in payload:
                details = f", files={len(payload['files'])}"
            if status == "api_error":
                err = str(payload.get("error", ""))[:180]
                details = f", error={err}"
            self._log(f"Month done: {label}, status={status}, took={elapsed:.1f}s{details}")

        source_elapsed = perf_counter() - source_started
        self._log(
            f"Source done: {source_name}, completed={completed}, skipped={skipped}, errors={errors}, took={source_elapsed:.1f}s"
        )
