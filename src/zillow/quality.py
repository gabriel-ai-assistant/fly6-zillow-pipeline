from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from .config import LOGS_DIR


def resolve_threshold(series_config: dict[str, Any]) -> float:
    default = 0.25 if series_config.get('category') == 'dynamics' else 0.15
    rules = series_config.get('quality_rules') or {}
    if isinstance(rules, dict) and 'mom_change_pct' in rules:
        return float(rules['mom_change_pct'])
    return default


def check_quality(rows: Iterable[dict[str, Any]], series_config: dict[str, Any], run_date: str | None = None) -> list[dict[str, Any]]:
    run_date = run_date or date.today().isoformat()
    threshold = resolve_threshold(series_config)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row['region_id'])].append(row)

    flagged: list[dict[str, Any]] = []
    for region_rows in grouped.values():
        region_rows.sort(key=lambda r: r['date'])
        prev = None
        for row in region_rows:
            value = row['value']
            if prev is None or prev == 0:
                prev = value
                continue
            change = (value - prev) / abs(prev)
            if abs(change) > threshold:
                flagged.append(
                    {
                        'series_key': series_config.get('series_key'),
                        'region_id': row['region_id'],
                        'region_name': row.get('region_name'),
                        'date': row['date'],
                        'value': value,
                        'prev_value': prev,
                        'mom_change': change,
                        'threshold': threshold,
                        'reason': f'abs_mom_change>{threshold:.2f}',
                    }
                )
            prev = value

    log_path = Path(LOGS_DIR) / f'anomalies_{run_date}.json'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text(encoding='utf-8'))
        except Exception:
            existing = []
    existing.extend(flagged)
    log_path.write_text(json.dumps(existing, indent=2, sort_keys=True), encoding='utf-8')

    return flagged
