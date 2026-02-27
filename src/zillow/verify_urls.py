from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from typing import Any

import requests

from .config import LOGS_DIR
from .download import load_datasets


def verify_url(url: str) -> dict[str, Any]:
    start = time.perf_counter()
    status = None
    ok = False
    try:
        response = requests.get(url, stream=True, timeout=20)
        status = response.status_code
        ok = response.status_code in {200, 206}
        response.close()
    except Exception:
        ok = False
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return {'url': url, 'status': status, 'ok': ok, 'ms': elapsed_ms}


def _mode_matches(required_for: str, mode: str) -> bool:
    return mode == 'both' or required_for in (mode, 'both')


def verify_all(mode: str, datasets_yml_path: str | Path | None = None) -> tuple[list[dict[str, Any]], int]:
    datasets = load_datasets(datasets_yml_path) if datasets_yml_path else load_datasets()
    datasets = [
        d
        for d in datasets
        if d.get('enabled', True) and _mode_matches(d.get('required_for', 'both'), mode)
    ]

    results: list[dict[str, Any]] = []
    for ds in datasets:
        result = verify_url(ds['source_url'])
        result.update({'series_key': ds.get('series_key'), 'required_for': ds.get('required_for')})
        results.append(result)

    run_date = date.today().isoformat()
    log_path = Path(LOGS_DIR) / f'url_verify_{run_date}.json'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding='utf-8')

    failures = [r for r in results if not r['ok']]
    exit_code = 1 if failures else 0
    return results, exit_code
