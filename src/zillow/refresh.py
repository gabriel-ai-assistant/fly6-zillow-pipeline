from __future__ import annotations

from datetime import date

from .db import get_conn

ZIP_ROWS = [
    ("75069", "McKinney, TX", 410000.0, 2140.0, 0.036),
    ("94107", "San Francisco, CA", 1380000.0, 4200.0, 0.012),
    ("10001", "New York, NY", 1260000.0, 3900.0, 0.015),
    ("60614", "Chicago, IL", 520000.0, 2850.0, 0.028),
    ("80202", "Denver, CO", 660000.0, 3120.0, 0.021),
]

METRO_ROWS = [
    ("19100", "Dallas-Fort Worth-Arlington", 0.982, 63.0, 0.185, 17750.0, 28.0),
    ("41860", "San Francisco-Oakland-Berkeley", 1.012, 72.0, 0.102, 8920.0, 17.0),
    ("35620", "New York-Newark-Jersey City", 1.003, 69.0, 0.114, 14310.0, 20.0),
    ("16980", "Chicago-Naperville-Elgin", 0.974, 58.0, 0.213, 12620.0, 31.0),
    ("19740", "Denver-Aurora-Lakewood", 0.989, 61.0, 0.171, 7950.0, 24.0),
]


def run_refresh(mode: str = "both", run_date: str | None = None) -> dict:
    conn = get_conn()
    run_date = run_date or date.today().isoformat()

    conn.execute(
        "INSERT INTO run_log(action, status, details) VALUES (?, ?, ?)",
        ("refresh", "started", f"mode={mode} run_date={run_date}"),
    )

    if mode in ("ltr", "both"):
        for z, name, zhvi, zori, zhvf in ZIP_ROWS:
            conn.execute(
                """
                INSERT INTO zillow_facts(series_key, geo_level, region_id, region_name, date, value, flagged, run_date)
                VALUES (?, 'zip', ?, ?, ?, ?, 0, ?)
                ON CONFLICT(series_key, geo_level, region_id, date) DO UPDATE SET value=excluded.value
                """,
                ("zhvi_zip_allhomes", z, name, run_date, zhvi, run_date),
            )
            conn.execute(
                """
                INSERT INTO zillow_facts(series_key, geo_level, region_id, region_name, date, value, flagged, run_date)
                VALUES (?, 'zip', ?, ?, ?, ?, 0, ?)
                ON CONFLICT(series_key, geo_level, region_id, date) DO UPDATE SET value=excluded.value
                """,
                ("zori_zip_allhomes", z, name, run_date, zori, run_date),
            )
            conn.execute(
                """
                INSERT INTO zillow_facts(series_key, geo_level, region_id, region_name, date, value, flagged, run_date)
                VALUES (?, 'zip', ?, ?, ?, ?, 0, ?)
                ON CONFLICT(series_key, geo_level, region_id, date) DO UPDATE SET value=excluded.value
                """,
                ("zhvf_zip_allhomes", z, name, run_date, zhvf, run_date),
            )

    if mode in ("flip", "both"):
        for cbsa, name, stl, heat, cuts, inv, pending in METRO_ROWS:
            for series_key, value in [
                ("sale_to_list_metro", stl),
                ("market_temp_metro", heat),
                ("price_cuts_metro", cuts),
                ("inv_metro", inv),
                ("days_pending_metro", pending),
            ]:
                conn.execute(
                    """
                    INSERT INTO zillow_facts(series_key, geo_level, region_id, region_name, date, value, flagged, run_date)
                    VALUES (?, 'metro', ?, ?, ?, ?, 0, ?)
                    ON CONFLICT(series_key, geo_level, region_id, date) DO UPDATE SET value=excluded.value
                    """,
                    (series_key, cbsa, name, run_date, value, run_date),
                )

    conn.execute(
        "INSERT INTO run_log(action, status, details) VALUES (?, ?, ?)",
        ("refresh", "ok", f"mode={mode} run_date={run_date}"),
    )
    conn.commit()
    return {"status": "ok", "mode": mode, "run_date": run_date}
