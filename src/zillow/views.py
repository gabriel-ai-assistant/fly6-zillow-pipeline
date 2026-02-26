"""Convenience accessors for SQLite analytics views."""

from __future__ import annotations

from typing import Any


def _rows_to_dicts(cursor: Any) -> list[dict]:
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def get_ltr_zip(conn, zip_code) -> dict | None:
    cur = conn.execute(
        "SELECT * FROM v_ltr_zip_latest WHERE zip = ? LIMIT 1",
        (str(zip_code),),
    )
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))


def get_flip_metro(conn, cbsa) -> dict | None:
    cur = conn.execute(
        "SELECT * FROM v_flip_metro_latest WHERE cbsa = ? LIMIT 1",
        (str(cbsa),),
    )
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))


def get_ltr_all_zips(conn) -> list[dict]:
    cur = conn.execute("SELECT * FROM v_ltr_zip_latest")
    return _rows_to_dicts(cur)


def get_flip_all_metros(conn) -> list[dict]:
    cur = conn.execute("SELECT * FROM v_flip_metro_latest")
    return _rows_to_dicts(cur)
