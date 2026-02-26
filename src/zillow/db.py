from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import db_path

_CONN: sqlite3.Connection | None = None


def get_conn() -> sqlite3.Connection:
    global _CONN
    if _CONN is None:
        path = db_path()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        _CONN = sqlite3.connect(path, check_same_thread=False)
        _CONN.row_factory = sqlite3.Row
    return _CONN


def close_conn() -> None:
    global _CONN
    if _CONN is not None:
        _CONN.close()
        _CONN = None
