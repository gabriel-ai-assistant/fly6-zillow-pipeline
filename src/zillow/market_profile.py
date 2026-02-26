"""Build combined LTR/flip market profiles."""

from __future__ import annotations

from .metrics import compute_ltr_metrics, get_yoy_value
from .views import get_flip_metro, get_ltr_zip


def _lookup_cbsa_for_zip(conn, zip_code: str) -> str | None:
    cur = conn.execute(
        "SELECT cbsa FROM zip_cbsa WHERE zip = ? ORDER BY res_ratio DESC LIMIT 1",
        (str(zip_code),),
    )
    row = cur.fetchone()
    return None if row is None else str(row[0])


def _choose_series_key(conn, zip_code: str, candidates: tuple[str, ...]) -> str | None:
    placeholders = ",".join("?" for _ in candidates)
    cur = conn.execute(
        f"""
        SELECT series_key
        FROM zillow_facts
        WHERE region_id = ?
          AND series_key IN ({placeholders})
        ORDER BY date DESC
        LIMIT 1
        """,
        (str(zip_code), *candidates),
    )
    row = cur.fetchone()
    return None if row is None else str(row[0])


def build_market_profile(conn, zip_code: str, strategy: str = None) -> dict:
    profile = {
        "zip": str(zip_code),
        "as_of": None,
        "ltr": None,
        "flip": None,
        "flip_null_reason": None,
    }

    strategy = None if strategy is None else strategy.lower().strip()
    include_ltr = strategy in (None, "ltr", "both")
    include_flip = strategy in (None, "flip", "both")
    ltr_row = None

    if include_ltr:
        ltr_row = get_ltr_zip(conn, zip_code)
        if ltr_row is None:
            profile["ltr"] = {
                "zhvi": None,
                "zori": None,
                "gross_yield": None,
                "zhvi_yoy": None,
                "zori_yoy": None,
                "data_available": False,
            }
        else:
            profile["as_of"] = ltr_row.get("zhvi_date") or ltr_row.get("zori_date")
            zhvi_series = _choose_series_key(conn, zip_code, ("zhvi_zip_allhomes", "zhvi_zip_sfr"))
            zori_series = _choose_series_key(conn, zip_code, ("zori_zip_allhomes", "zori_zip_sfr"))
            zhvi_prev = (
                get_yoy_value(conn, zip_code, zhvi_series, ltr_row.get("zhvi_date")) if zhvi_series else None
            )
            zori_prev = (
                get_yoy_value(conn, zip_code, zori_series, ltr_row.get("zori_date")) if zori_series else None
            )
            metrics = compute_ltr_metrics(
                zhvi=ltr_row.get("zhvi"),
                zori=ltr_row.get("zori"),
                zhvi_prev_year=zhvi_prev,
                zori_prev_year=zori_prev,
            )
            profile["ltr"] = {
                "zhvi": ltr_row.get("zhvi"),
                "zori": ltr_row.get("zori"),
                "gross_yield": metrics.get("gross_yield"),
                "zhvi_yoy": metrics.get("zhvi_yoy"),
                "zori_yoy": metrics.get("zori_yoy"),
                "data_available": True,
            }

    if include_flip:
        cbsa = _lookup_cbsa_for_zip(conn, zip_code)
        if cbsa is None:
            profile["flip"] = None
            profile["flip_null_reason"] = "metro_mapping_unavailable"
        else:
            flip_row = get_flip_metro(conn, cbsa)
            if flip_row is None:
                profile["flip"] = None
                profile["flip_null_reason"] = "no_metro_data"
            else:
                profile["flip"] = {
                    "cbsa": str(flip_row.get("cbsa")),
                    "metro_name": flip_row.get("metro_name"),
                    "sale_to_list": flip_row.get("sale_to_list"),
                    "market_heat": flip_row.get("market_heat"),
                    "price_cut_pct": flip_row.get("price_cut_pct"),
                    "days_to_pending": flip_row.get("days_to_pending"),
                    "inventory": flip_row.get("inventory"),
                    "data_available": True,
                }
                if profile["as_of"] is None:
                    profile["as_of"] = ltr_row.get("zhvi_date") if include_ltr and ltr_row else None

    return profile
