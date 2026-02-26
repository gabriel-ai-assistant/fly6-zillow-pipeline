from __future__ import annotations

import os
from pathlib import Path


DEFAULT_ROOT = Path("fly6_data") / "zillow"


def data_root() -> Path:
    return Path(os.getenv("ZILLOW_DATA_ROOT", DEFAULT_ROOT)).resolve()


def db_path() -> Path:
    return Path(os.getenv("ZILLOW_DB_PATH", data_root() / "db" / "zillow.sqlite")).resolve()


def datasets_path() -> Path:
    return data_root() / "datasets.yml"


def schema_path() -> Path:
    return data_root() / "db" / "schema.sql"


def logs_dir() -> Path:
    return data_root() / "logs"


def geo_dir() -> Path:
    return data_root() / "geo"
