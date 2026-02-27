from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.config import IngestionConfig  # noqa: E402
from src.preprocessing.pipeline import PreprocessingPipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run preprocessing pipeline")
    parser.add_argument("--config", default="config/bengaluru_2020_2024.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = PROJECT_ROOT
    config = IngestionConfig.from_json(project_root / args.config)
    pipeline = PreprocessingPipeline(project_root=project_root, config=config)
    pipeline.run()
    print(f"Preprocessing completed for {config.city}.")


if __name__ == "__main__":
    main()
