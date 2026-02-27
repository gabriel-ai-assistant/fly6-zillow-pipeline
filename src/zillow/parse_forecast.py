from __future__ import annotations

import csv
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterator

from .config import LOGS_DIR
from .drift import check_drift


def _append_headers_log(run_date: str, payload: dict) -> None:
    path = Path(LOGS_DIR) / f'headers_{run_date}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            existing = []
    existing.append(payload)
    path.write_text(json.dumps(existing, indent=2, sort_keys=True), encoding='utf-8')


def _add_months(base_date: date, months: int) -> date:
    year = base_date.year + (base_date.month - 1 + months) // 12
    month = (base_date.month - 1 + months) % 12 + 1
    next_month = date(year + (month // 12), (month % 12) + 1, 1) if month == 12 else date(year, month + 1, 1)
    month_end = (next_month - timedelta(days=1)).day
    day = min(base_date.day, month_end)
    return date(year, month, day)


def _to_float(raw: str) -> float | None:
    value = raw.strip()
    if value in {'', 'NA', 'NaN', 'null', 'None'}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_forecast(csv_path: str | Path, series_config: dict, run_date: str | None = None) -> Iterator[tuple[str, str, str, float]]:
    run_date = run_date or date.today().isoformat()
    path = Path(csv_path)
    check_drift(path, series_config, run_date=run_date)

    region_id_col = series_config.get('region_id_column', 'RegionID')
    region_name_col = series_config.get('region_name_column', 'RegionName')
    date_pattern = re.compile(series_config.get('date_column_regex', r'^\d{4}-\d{2}-\d{2}$'))
    horizon_pattern = re.compile(r'^[+]?([0-9]+)M$')

    with path.open('r', encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        _append_headers_log(run_date, {
            'series_key': series_config.get('series_key'),
            'csv_path': str(path),
            'headers': headers,
        })

        forecast_columns = [h for h in headers if h and (date_pattern.match(h) or horizon_pattern.match(h))]

        for row in reader:
            region_id = (row.get(region_id_col) or '').strip()
            region_name = (row.get(region_name_col) or '').strip()
            if not region_id:
                continue

            base_date_raw = (row.get('BaseDate') or '').strip()
            base_date = None
            if base_date_raw:
                try:
                    base_date = datetime.strptime(base_date_raw[:10], '%Y-%m-%d').date()
                except ValueError:
                    base_date = None

            for col in forecast_columns:
                output_date: str | None = None
                if date_pattern.match(col):
                    output_date = col
                else:
                    match = horizon_pattern.match(col)
                    if match and base_date is not None:
                        output_date = _add_months(base_date, int(match.group(1))).isoformat()

                if not output_date:
                    continue

                value = _to_float(row.get(col, ''))
                if value is None:
                    continue
                yield (region_id, region_name, output_date, value)
