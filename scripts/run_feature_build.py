from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.dataset_builder import FeatureBuilder  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build model-ready flood dataset")
    parser.add_argument("--city", default="bengaluru")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = PROJECT_ROOT
    builder = FeatureBuilder(project_root=project_root, city=args.city)
    out_path = builder.run()
    print(f"Feature dataset created at: {out_path}")


if __name__ == "__main__":
    main()
