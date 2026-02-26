"""Similarity search for ZIP markets."""

from __future__ import annotations

import math

from .metrics import compute_ltr_metrics, get_yoy_value
from .views import get_ltr_zip


def _feature_row(conn, zip_code: str) -> dict | None:
    row = get_ltr_zip(conn, zip_code)
    if row is None:
        return None

    zhvi_prev = get_yoy_value(conn, zip_code, "zhvi_zip_allhomes", row.get("zhvi_date"))
    zori_prev = get_yoy_value(conn, zip_code, "zori_zip_allhomes", row.get("zori_date"))
    metrics = compute_ltr_metrics(row.get("zhvi"), row.get("zori"), zhvi_prev, zori_prev)

    return {
        "zip": str(zip_code),
        "zhvi": row.get("zhvi"),
        "zori": row.get("zori"),
        "gross_yield": metrics.get("gross_yield"),
        "zhvi_yoy": metrics.get("zhvi_yoy"),
        "zori_yoy": metrics.get("zori_yoy"),
    }


def _standardize(rows: list[dict], keys: list[str]) -> list[dict]:
    means = {}
    stds = {}

    for key in keys:
        vals = [r[key] for r in rows if r[key] is not None]
        if not vals:
            means[key] = 0.0
            stds[key] = 1.0
            continue
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = math.sqrt(var) or 1.0
        means[key] = mean
        stds[key] = std

    out = []
    for r in rows:
        zr = dict(r)
        for key in keys:
            val = r[key]
            zr[f"z_{key}"] = 0.0 if val is None else (val - means[key]) / stds[key]
        out.append(zr)
    return out


def similar_zips(
    conn,
    seed_zip: str,
    candidate_zips: list[str],
    k: int = 5,
) -> list[dict]:
    features = ["zhvi", "zori", "gross_yield", "zhvi_yoy", "zori_yoy"]

    seed = _feature_row(conn, seed_zip)
    if seed is None:
        return []

    rows = [seed]
    for zip_code in candidate_zips:
        if str(zip_code) == str(seed_zip):
            continue
        fr = _feature_row(conn, zip_code)
        if fr is not None:
            rows.append(fr)

    zrows = _standardize(rows, features)
    seed_z = next(r for r in zrows if r["zip"] == str(seed_zip))

    scored = []
    for row in zrows:
        if row["zip"] == str(seed_zip):
            continue
        dist = math.sqrt(sum((row[f"z_{f}"] - seed_z[f"z_{f}"]) ** 2 for f in features))
        scored.append({"zip": row["zip"], "distance": dist})

    scored.sort(key=lambda x: x["distance"])
    return scored[:k]
