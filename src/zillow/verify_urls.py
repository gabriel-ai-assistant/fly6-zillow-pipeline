from __future__ import annotations

import json
from datetime import date

import requests
import yaml

from .config import datasets_path, logs_dir


def _required_for_mode(required_for: str, mode: str) -> bool:
    if mode == "both":
        return required_for in ("ltr", "flip", "both")
    return required_for in (mode, "both")


def verify_all(mode: str = "both", timeout: int = 15) -> dict:
    mode = (mode or "both").lower()
    cfg = yaml.safe_load(datasets_path().read_text(encoding="utf-8")) or {}
    checks = []
    required_failures = []

    for row in cfg.get("datasets", []):
        if not row.get("enabled", True):
            continue
        series_key = row.get("series_key")
        required_for = row.get("required_for", "both")
        url = row.get("source_url")
        required = _required_for_mode(required_for, mode)

        ok = False
        status_code = None
        error = None
        try:
            r = requests.get(url, timeout=timeout)
            status_code = r.status_code
            ok = r.ok
        except Exception as exc:
            error = str(exc)

        result = {
            "series_key": series_key,
            "url": url,
            "required": required,
            "ok": ok,
            "status_code": status_code,
            "error": error,
        }
        checks.append(result)
        if required and not ok:
            required_failures.append(series_key)

    out = {
        "mode": mode,
        "date": date.today().isoformat(),
        "checks": checks,
        "required_failed": required_failures,
        "ok": len(required_failures) == 0,
    }
    logs_dir().mkdir(parents=True, exist_ok=True)
    (logs_dir() / f"url_verify_{date.today().isoformat()}.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    return out
