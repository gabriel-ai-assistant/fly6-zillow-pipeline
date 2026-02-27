from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from typing import Any

import requests
import yaml

from .config import DATASETS_YML_PATH, RAW_DIR, ensure_data_dirs


def load_datasets(datasets_yml_path: Path | str = DATASETS_YML_PATH) -> list[dict[str, Any]]:
    path = Path(datasets_yml_path)
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    if isinstance(data, dict) and 'datasets' in data:
        datasets = data['datasets']
    elif isinstance(data, list):
        datasets = data
    else:
        raise ValueError(f'Unexpected datasets format in {path}')
    return [item for item in datasets if isinstance(item, dict)]


def _mode_matches(required_for: str, mode: str) -> bool:
    return mode == 'both' or required_for in (mode, 'both')


def download_series(series_config: dict[str, Any], run_date: str, raw_dir: Path | str = RAW_DIR) -> Path:
    series_key = series_config['series_key']
    url = series_config['source_url']
    out_dir = Path(raw_dir) / run_date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'{series_key}.csv'
    tmp_path = out_dir / f'{series_key}.csv.tmp'

    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            headers = {
                "User-Agent": "Fly6Holdings-DataSync/1.0 (gabriel.opus.soong@gmail.com)",
                "Accept": "text/csv,application/octet-stream,*/*",
            }
            with requests.get(url, stream=True, timeout=60, headers=headers) as response:
                if response.status_code == 404:
                    raise FileNotFoundError(f'404 for {series_key}: {url}')
                response.raise_for_status()
                with tmp_path.open('wb') as fh:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            fh.write(chunk)
            tmp_path.replace(out_path)
            return out_path
        except FileNotFoundError:
            raise
        except Exception:
            if attempt >= attempts:
                raise
            time.sleep(2 ** (attempt - 1))

    raise RuntimeError(f'Failed to download {series_key}')


def write_manifest(raw_dir: Path | str, run_date: str, manifest: dict[str, Any]) -> Path:
    out_path = Path(raw_dir) / run_date / 'manifest.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding='utf-8')
    return out_path


def download_all(mode: str, run_date: str | None = None) -> dict[str, Any]:
    ensure_data_dirs()
    run_date = run_date or date.today().isoformat()
    datasets = [
        d
        for d in load_datasets(DATASETS_YML_PATH)
        if d.get('enabled', True) and _mode_matches(d.get('required_for', 'both'), mode)
    ]

    manifest: dict[str, Any] = {'run_date': run_date, 'mode': mode, 'series': {}}
    for ds in datasets:
        series_key = ds['series_key']
        try:
            csv_path = download_series(ds, run_date, RAW_DIR)
            manifest['series'][series_key] = {
                'status': 'ok',
                'path': str(csv_path),
                'url': ds['source_url'],
            }
        except Exception as exc:
            manifest['series'][series_key] = {
                'status': 'error',
                'path': None,
                'url': ds.get('source_url'),
                'error': str(exc),
            }
    write_manifest(RAW_DIR, run_date, manifest)
    return manifest
