from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterator

from .drift import check_drift


def _to_float(raw: str) -> float | None:
    value = raw.strip()
    if value in {'', 'NA', 'NaN', 'null', 'None'}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_wide(csv_path: str | Path, series_config: dict) -> Iterator[tuple[str, str, str, float]]:
    path = Path(csv_path)
    check_drift(path, series_config)

    date_pattern = re.compile(series_config.get('date_column_regex', r'^\d{4}-\d{2}-\d{2}$'))
    region_id_col = series_config.get('region_id_column', 'RegionID')
    region_name_col = series_config.get('region_name_column', 'RegionName')

    with path.open('r', encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            return

        date_columns = [c for c in reader.fieldnames if c and date_pattern.match(c)]
        for row in reader:
            region_id = (row.get(region_id_col) or '').strip()
            region_name = (row.get(region_name_col) or '').strip()
            if not region_id:
                continue

            for col in date_columns:
                raw = row.get(col, '')
                value = _to_float(raw)
                if value is None:
                    continue
                yield (region_id, region_name, col, value)
