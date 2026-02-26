from __future__ import annotations

import yaml

from .config import datasets_path, schema_path
from .db import get_conn


def init_db() -> None:
    conn = get_conn()
    schema = schema_path().read_text(encoding="utf-8")
    conn.executescript(schema)

    cfg = yaml.safe_load(datasets_path().read_text(encoding="utf-8")) or {}
    for row in cfg.get("datasets", []):
        conn.execute(
            """
            INSERT INTO series_meta(series_key, category, geo_level, unit, series_name, required_for, enabled, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(series_key) DO UPDATE SET
              category=excluded.category,
              geo_level=excluded.geo_level,
              unit=excluded.unit,
              series_name=excluded.series_name,
              required_for=excluded.required_for,
              enabled=excluded.enabled,
              source_url=excluded.source_url
            """,
            (
                row.get("series_key"),
                row.get("category"),
                row.get("geo_level"),
                row.get("unit"),
                row.get("series_name"),
                row.get("required_for"),
                1 if row.get("enabled", True) else 0,
                row.get("source_url"),
            ),
        )

    conn.execute(
        "INSERT INTO run_log(action, status, details) VALUES (?, ?, ?)",
        ("init", "ok", "schema applied and series_meta seeded"),
    )
    conn.commit()
