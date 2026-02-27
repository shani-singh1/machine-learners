from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REQUIRED_ENV_KEYS = (
    "CDS_API_KEY",
    "CDSE_CLIENT_ID",
    "CDSE_CLIENT_SECRET",
    "GEE_PROJECT_ID",
)


def load_env_file(project_root: Path) -> None:
    env_path = project_root / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized_key = key.strip()
        normalized_value = value.strip().strip("'").strip('"')
        os.environ.setdefault(normalized_key, normalized_value)


@dataclass(frozen=True)
class AppSettings:
    project_root: Path
    cds_api_key: str
    cdse_client_id: str
    cdse_client_secret: str
    gee_project_id: str

    @staticmethod
    def from_env(project_root: Path | None = None) -> "AppSettings":
        root = project_root or Path(__file__).resolve().parents[2]
        load_env_file(root)
        missing = [key for key in REQUIRED_ENV_KEYS if not os.getenv(key)]
        if missing:
            joined = ", ".join(sorted(missing))
            raise RuntimeError(f"Missing required environment variables: {joined}")

        return AppSettings(
            project_root=root,
            cds_api_key=os.environ["CDS_API_KEY"],
            cdse_client_id=os.environ["CDSE_CLIENT_ID"],
            cdse_client_secret=os.environ["CDSE_CLIENT_SECRET"],
            gee_project_id=os.environ["GEE_PROJECT_ID"],
        )


def mask_secret(value: str, visible_chars: int = 3) -> str:
    if not value:
        return ""
    if len(value) <= visible_chars:
        return "*" * len(value)
    return f"{value[:visible_chars]}{'*' * (len(value) - visible_chars)}"


def explain_loaded_keys(keys: Iterable[str]) -> str:
    return ", ".join(sorted(keys))
