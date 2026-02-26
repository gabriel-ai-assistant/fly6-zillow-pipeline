"""Metrics and time-series utilities for Zillow analytics."""

from __future__ import annotations

from datetime import date
from typing import Any


def _safe_ratio(num: float | None, den: float | None) -> float | None:
    if num is None or den in (None, 0):
        return None
    return num / den


def _coerce_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _shift_year(value: Any, years: int = 1) -> str:
    d = _coerce_date(value)
    try:
        return d.replace(year=d.year - years).isoformat()
    except ValueError:
        return d.replace(year=d.year - years, day=28).isoformat()


def compute_ltr_metrics(
    zhvi: float,
    zori: float,
    zhvi_prev_year: float = None,
    zori_prev_year: float = None,
) -> dict:
    gross_yield = _safe_ratio((zori or 0) * 12.0 if zori is not None else None, zhvi)
    zhvi_yoy = None
    zori_yoy = None

    if zhvi is not None and zhvi_prev_year not in (None, 0):
        zhvi_yoy = (zhvi - zhvi_prev_year) / zhvi_prev_year
    if zori is not None and zori_prev_year not in (None, 0):
        zori_yoy = (zori - zori_prev_year) / zori_prev_year

    return {
        "gross_yield": gross_yield,
        "zhvi_yoy": zhvi_yoy,
        "zori_yoy": zori_yoy,
        "monthly_mom": None,
    }


def compute_flip_metrics(
    sale_to_list,
    price_cut_pct,
    days_pending,
    inventory,
    new_listings,
) -> dict:
    # Heuristic normalization ranges for comparability.
    stl_norm = 0.0 if sale_to_list is None else max(0.0, min(1.0, (sale_to_list - 0.9) / 0.2))
    days_inv = 0.0 if days_pending is None else max(0.0, min(1.0, (90.0 - days_pending) / 90.0))
    demand_score = (stl_norm + days_inv) / 2.0

    inv_norm = 0.0 if inventory is None else max(0.0, min(1.0, inventory / 50000.0))
    new_norm = 0.0 if new_listings is None else max(0.0, min(1.0, new_listings / 10000.0))
    supply_score = (inv_norm + new_norm) / 2.0

    price_pressure = 0.0 if price_cut_pct is None else max(0.0, min(1.0, 1.0 - price_cut_pct))

    return {
        "demand_score": demand_score,
        "supply_score": supply_score,
        "price_pressure": price_pressure,
    }


def get_zip_time_series(conn, zip_code, series_key, lookback_months=24) -> list[dict]:
    cur = conn.execute(
        """
        SELECT region_id AS zip, region_name, date, value, flagged
        FROM zillow_facts
        WHERE region_id = ?
          AND series_key = ?
        ORDER BY date DESC
        LIMIT ?
        """,
        (str(zip_code), str(series_key), int(lookback_months)),
    )
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    rows.sort(key=lambda x: x["date"])
    return rows


def get_yoy_value(conn, zip_code, series_key, current_date) -> float | None:
    target_date = _shift_year(current_date, years=1)
    cur = conn.execute(
        """
        SELECT value
        FROM zillow_facts
        WHERE region_id = ?
          AND series_key = ?
          AND date <= ?
        ORDER BY date DESC
        LIMIT 1
        """,
        (str(zip_code), str(series_key), target_date),
    )
    row = cur.fetchone()
    return None if row is None else row[0]
