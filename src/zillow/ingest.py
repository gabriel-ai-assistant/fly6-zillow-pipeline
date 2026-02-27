from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .config import DB_PATH, RAW_DIR, REPO_ROOT, ensure_data_dirs
from .download import load_datasets
from .parse_forecast import parse_forecast
from .parse_wide import parse_wide
from .quality import resolve_threshold


def _schema_path() -> Path:
    repo_schema = REPO_ROOT / 'fly6_data' / 'zillow' / 'db' / 'schema.sql'
    if repo_schema.exists():
        return repo_schema
    return Path(DB_PATH).parent / 'schema.sql'


def init_db(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    ensure_data_dirs()
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')

    conn.executescript(_schema_path().read_text(encoding='utf-8'))

    datasets = load_datasets(REPO_ROOT / 'fly6_data' / 'zillow' / 'datasets.yml')
    for ds in datasets:
        conn.execute(
            '''
            INSERT OR REPLACE INTO series_meta (
              series_key, category, geo_level, unit, series_name, required_for,
              enabled, source_url, region_id_column, region_name_column,
              region_columns_json, date_column_regex, quality_rules_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                ds.get('series_key'),
                ds.get('category'),
                ds.get('geo_level'),
                ds.get('unit'),
                ds.get('series_name'),
                ds.get('required_for', 'both'),
                int(bool(ds.get('enabled', True))),
                ds.get('source_url'),
                ds.get('region_id_column'),
                ds.get('region_name_column'),
                json.dumps(ds.get('region_columns', [])),
                ds.get('date_column_regex', r'^\\d{4}-\\d{2}-\\d{2}$'),
                json.dumps(ds.get('quality_rules', {})),
            ),
        )

    conn.commit()
    return conn


def ingest_series(conn: sqlite3.Connection, series_config: dict[str, Any], csv_path: Path | str, run_date: str) -> tuple[int, int]:
    parser = parse_forecast if series_config.get('category') == 'zhvf' else parse_wide
    threshold = resolve_threshold(series_config)

    rows_upserted = 0
    rows_flagged = 0
    prev_by_region: dict[str, float] = {}

    for region_id, region_name, point_date, value in parser(csv_path, series_config):
        flagged = 0
        reason = None
        prev = prev_by_region.get(region_id)
        if prev is not None and prev != 0:
            change = (value - prev) / abs(prev)
            if abs(change) > threshold:
                flagged = 1
                rows_flagged += 1
                reason = f'abs_mom_change>{threshold:.2f}'
        prev_by_region[region_id] = value

        conn.execute(
            '''
            INSERT OR REPLACE INTO zillow_facts
              (series_key, geo_level, region_id, region_name, date, value, flagged, flag_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                series_config['series_key'],
                series_config['geo_level'],
                region_id,
                region_name,
                point_date,
                value,
                flagged,
                reason,
            ),
        )
        rows_upserted += 1

    conn.commit()
    return rows_upserted, rows_flagged


def _mode_matches(required_for: str, mode: str) -> bool:
    return mode == 'both' or required_for in (mode, 'both')


def ingest_all(mode: str, run_date: str | None = None) -> dict[str, Any]:
    run_date = run_date or date.today().isoformat()
    run_id = str(uuid.uuid4())
    conn = init_db(DB_PATH)

    datasets = [
        d
        for d in load_datasets(REPO_ROOT / 'fly6_data' / 'zillow' / 'datasets.yml')
        if d.get('enabled', True) and _mode_matches(d.get('required_for', 'both'), mode)
    ]

    summary: dict[str, Any] = {'run_id': run_id, 'run_date': run_date, 'mode': mode, 'series': {}}

    for ds in datasets:
        series_key = ds['series_key']
        csv_path = Path(RAW_DIR) / run_date / f'{series_key}.csv'
        started_at = datetime.utcnow().isoformat(timespec='seconds')

        if not csv_path.exists():
            conn.execute(
                '''
                INSERT INTO run_log (run_id, run_date, mode, series_key, status, error_msg, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    run_id,
                    run_date,
                    mode,
                    series_key,
                    'missing_file',
                    f'missing raw file: {csv_path}',
                    started_at,
                    datetime.utcnow().isoformat(timespec='seconds'),
                ),
            )
            summary['series'][series_key] = {'status': 'missing_file', 'rows_upserted': 0, 'rows_flagged': 0}
            continue

        try:
            rows_upserted, rows_flagged = ingest_series(conn, ds, csv_path, run_date)
            status = 'ok'
            error_msg = None
        except Exception as exc:
            rows_upserted, rows_flagged = 0, 0
            status = 'error'
            error_msg = str(exc)

        conn.execute(
            '''
            INSERT INTO run_log
              (run_id, run_date, mode, series_key, status, rows_upserted, rows_flagged, error_msg, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                run_id,
                run_date,
                mode,
                series_key,
                status,
                rows_upserted,
                rows_flagged,
                error_msg,
                started_at,
                datetime.utcnow().isoformat(timespec='seconds'),
            ),
        )
        summary['series'][series_key] = {
            'status': status,
            'rows_upserted': rows_upserted,
            'rows_flagged': rows_flagged,
            'error': error_msg,
        }

    conn.commit()
    conn.close()
    return summary
