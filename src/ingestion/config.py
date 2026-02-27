from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date


@dataclass(frozen=True)
class RegionOfInterest:
    name: str
    bbox_wgs84: tuple[float, float, float, float]


@dataclass(frozen=True)
class IngestionConfig:
    city: str
    country: str
    date_range: DateRange
    roi: RegionOfInterest
    sources: dict[str, bool]

    @staticmethod
    def from_json(path: Path) -> "IngestionConfig":
        payload = json.loads(path.read_text(encoding="utf-8"))
        start = date.fromisoformat(payload["date_range"]["start"])
        end = date.fromisoformat(payload["date_range"]["end"])
        bbox = tuple(payload["roi"]["bbox_wgs84"])
        if len(bbox) != 4:
            raise ValueError("roi.bbox_wgs84 must have exactly four coordinates")

        return IngestionConfig(
            city=payload["city"],
            country=payload["country"],
            date_range=DateRange(start=start, end=end),
            roi=RegionOfInterest(
                name=payload["roi"]["name"],
                bbox_wgs84=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
            ),
            sources={k: bool(v) for k, v in payload["sources"].items()},
        )
