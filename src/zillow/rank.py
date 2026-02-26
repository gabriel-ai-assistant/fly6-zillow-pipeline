"""Ranking helpers for LTR and flip strategies."""

from __future__ import annotations

from .market_profile import _lookup_cbsa_for_zip
from .metrics import compute_ltr_metrics, get_yoy_value
from .views import get_flip_metro, get_ltr_zip


def _latest_value(conn, zip_code: str, series_keys: tuple[str, ...]) -> float | None:
    placeholders = ",".join("?" for _ in series_keys)
    cur = conn.execute(
        f"""
        SELECT value
        FROM zillow_facts
        WHERE region_id = ?
          AND series_key IN ({placeholders})
        ORDER BY date DESC
        LIMIT 1
        """,
        (str(zip_code), *series_keys),
    )
    row = cur.fetchone()
    return None if row is None else row[0]


def rank_zips_for_ltr(
    conn,
    zips: list[str],
    zhvi_max: float = None,
    yield_min: float = None,
    zori_yoy_min: float = None,
    sort_by: str = "gross_yield",
    top_n: int = 10,
) -> list[dict]:
    ranked: list[dict] = []

    for zip_code in zips:
        row = get_ltr_zip(conn, zip_code)
        if row is None:
            continue

        zhvi_prev = get_yoy_value(conn, zip_code, "zhvi_zip_allhomes", row.get("zhvi_date"))
        zori_prev = get_yoy_value(conn, zip_code, "zori_zip_allhomes", row.get("zori_date"))
        metrics = compute_ltr_metrics(row.get("zhvi"), row.get("zori"), zhvi_prev, zori_prev)

        out = {
            "zip": str(zip_code),
            "region_name": row.get("region_name"),
            "zhvi": row.get("zhvi"),
            "zori": row.get("zori"),
            "gross_yield": metrics.get("gross_yield"),
            "zhvi_yoy": metrics.get("zhvi_yoy"),
            "zori_yoy": metrics.get("zori_yoy"),
        }

        if zhvi_max is not None and (out["zhvi"] is None or out["zhvi"] > zhvi_max):
            continue
        if yield_min is not None and (out["gross_yield"] is None or out["gross_yield"] < yield_min):
            continue
        if zori_yoy_min is not None and (out["zori_yoy"] is None or out["zori_yoy"] < zori_yoy_min):
            continue

        ranked.append(out)

    ranked.sort(key=lambda x: (x.get(sort_by) is None, x.get(sort_by)), reverse=True)
    return ranked[:top_n]


def rank_metros_for_flip(
    conn,
    cbsa_list: list[str],
    sort_by: str = "sale_to_list",
    top_n: int = 10,
) -> list[dict]:
    allowed = {"sale_to_list", "market_heat", "days_to_pending", "price_cut_pct"}
    if sort_by not in allowed:
        sort_by = "sale_to_list"

    rows = []
    for cbsa in cbsa_list:
        row = get_flip_metro(conn, cbsa)
        if row is None:
            continue
        rows.append(row)

    reverse = sort_by != "days_to_pending"
    rows.sort(key=lambda x: (x.get(sort_by) is None, x.get(sort_by)), reverse=reverse)
    return rows[:top_n]


def select_zips_within_metro_for_flip(
    conn,
    cbsa: str,
    zips_in_cbsa: list[str],
    zhvi_min: float = None,
    zhvi_max: float = None,
    require_positive_zhvf: bool = False,
    top_n: int = 10,
) -> list[dict]:
    selected: list[dict] = []

    for zip_code in zips_in_cbsa:
        mapped = _lookup_cbsa_for_zip(conn, zip_code)
        if mapped != str(cbsa):
            continue

        ltr = get_ltr_zip(conn, zip_code)
        if ltr is None:
            continue

        zhvi = ltr.get("zhvi")
        if zhvi_min is not None and (zhvi is None or zhvi < zhvi_min):
            continue
        if zhvi_max is not None and (zhvi is None or zhvi > zhvi_max):
            continue

        zhvf = _latest_value(conn, zip_code, ("zhvf_zip_allhomes", "zhvf_zip_sfr"))
        if require_positive_zhvf and (zhvf is None or zhvf <= 0):
            continue

        selected.append(
            {
                "zip": str(zip_code),
                "region_name": ltr.get("region_name"),
                "zhvi": zhvi,
                "zhvf": zhvf,
                "gross_yield": ltr.get("gross_yield"),
            }
        )

    selected.sort(key=lambda x: (x.get("zhvf") is None, x.get("zhvf"), x.get("gross_yield")), reverse=True)
    return selected[:top_n]
