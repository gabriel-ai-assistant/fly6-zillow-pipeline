from __future__ import annotations

import os
from pathlib import Path


DEFAULT_ROOT = Path("fly6_data") / "zillow"
PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "fly6_data" / "zillow"


def data_root() -> Path:
    return Path(os.getenv("ZILLOW_DATA_ROOT", DEFAULT_ROOT)).resolve()


def db_path() -> Path:
    return Path(os.getenv("ZILLOW_DB_PATH", data_root() / "db" / "zillow.sqlite")).resolve()


def datasets_path() -> Path:
    primary = data_root() / "datasets.yml"
    return primary if primary.exists() else (PACKAGE_ROOT / "datasets.yml")


def schema_path() -> Path:
    primary = data_root() / "db" / "schema.sql"
    return primary if primary.exists() else (PACKAGE_ROOT / "db" / "schema.sql")


def logs_dir() -> Path:
    return data_root() / "logs"


def geo_dir() -> Path:
    return data_root() / "geo"
