from __future__ import annotations

import csv

from .config import geo_dir
from .db import get_conn


def build_zip_to_cbsa() -> dict:
    csv_path = geo_dir() / "zip_to_cbsa.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"missing crosswalk file: {csv_path}")

    conn = get_conn()
    rows = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    best = {}
    for row in rows:
        z = str(row.get("zip", "")).zfill(5)
        cur = best.get(z)
        try:
            score = float(row.get("res_ratio") or 0.0)
        except ValueError:
            score = 0.0
        if cur is None or score > cur[0]:
            best[z] = (score, row)

    for z, (_, row) in best.items():
        conn.execute(
            """
            INSERT INTO zip_cbsa(zip, cbsa, cbsa_name, state, res_ratio, bus_ratio, oth_ratio)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(zip, cbsa) DO UPDATE SET
              cbsa_name=excluded.cbsa_name,
              state=excluded.state,
              res_ratio=excluded.res_ratio,
              bus_ratio=excluded.bus_ratio,
              oth_ratio=excluded.oth_ratio
            """,
            (
                z,
                str(row.get("cbsa", "")),
                row.get("cbsa_name"),
                row.get("state"),
                float(row.get("res_ratio") or 0.0),
                float(row.get("bus_ratio") or 0.0),
                float(row.get("oth_ratio") or 0.0),
            ),
        )

    conn.execute(
        "INSERT INTO run_log(action, status, details) VALUES (?, ?, ?)",
        ("build-zip-cbsa", "ok", f"loaded {len(best)} ZIPs"),
    )
    conn.commit()
    return {"loaded": len(best)}
