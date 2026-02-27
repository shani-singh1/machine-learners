from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import AppSettings, explain_loaded_keys  # noqa: E402
from src.ingestion.config import IngestionConfig  # noqa: E402
from src.ingestion.pipeline import IngestionPipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run flood project ingestion pipeline")
    parser.add_argument(
        "--config",
        default="config/bengaluru_2020_2024.json",
        help="Path to ingestion config json",
    )
    parser.add_argument(
        "--live-fetch",
        action="store_true",
        help="If set, calls CDSE API for Sentinel sources.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = PROJECT_ROOT
    config_path = project_root / args.config

    settings = AppSettings.from_env(project_root=project_root)
    config = IngestionConfig.from_json(config_path)

    print(
        "Loaded env keys: "
        + explain_loaded_keys(["CDS_API_KEY", "CDSE_CLIENT_ID", "CDSE_CLIENT_SECRET", "GEE_PROJECT_ID"])
    )
    print(
        f"Running ingestion for {config.city} from "
        f"{config.date_range.start.isoformat()} to {config.date_range.end.isoformat()}"
    )

    pipeline = IngestionPipeline(settings=settings, config=config, live_fetch=args.live_fetch)
    pipeline.run()
    print("Ingestion completed.")


if __name__ == "__main__":
    main()
