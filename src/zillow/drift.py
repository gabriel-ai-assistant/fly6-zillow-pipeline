from __future__ import annotations

import csv
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .config import LOGS_DIR


def _append_json_log(path: Path, payload: dict[str, Any]) -> None:
    existing: list[dict[str, Any]] = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            existing = []
    existing.append(payload)
    path.write_text(json.dumps(existing, indent=2, sort_keys=True), encoding='utf-8')


def check_drift(csv_path: str | Path, series_config: dict[str, Any], run_date: str | None = None) -> dict[str, Any]:
    run_date = run_date or date.today().isoformat()
    path = Path(csv_path)
    with path.open('r', encoding='utf-8-sig', newline='') as fh:
        reader = csv.reader(fh)
        headers = next(reader)

    expected_region = series_config.get('region_columns', [])
    date_regex = re.compile(series_config.get('date_column_regex', r'^\d{4}-\d{2}-\d{2}$'))

    actual_region = [h for h in headers if h in expected_region]
    date_like = [h for h in headers if date_regex.match(h)]
    tolerated = set(expected_region) | set(date_like) | {'BaseDate'}
    tolerated |= {h for h in headers if re.match(r'^[+]?\d+M$', h)}

    unknown_columns = [h for h in headers if h not in tolerated]
    missing_region = [h for h in expected_region if h not in headers]

    finding = {
        'series_key': series_config.get('series_key'),
        'csv_path': str(path),
        'missing_region_columns': missing_region,
        'unknown_columns': unknown_columns,
        'region_column_count': len(actual_region),
        'date_column_count': len(date_like),
        'ok': not missing_region and not unknown_columns,
    }

    log_path = Path(LOGS_DIR) / f'drift_{run_date}.json'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _append_json_log(log_path, finding)
    return finding
