"""Fly 6 Holdings — Zillow Pipeline API"""
from __future__ import annotations

import asyncio
import sqlite3
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys, os
sys.path.insert(0, "/app")

from src.zillow import config
from src.zillow.market_profile import build_market_profile
from src.zillow.rank import rank_zips_for_ltr, rank_metros_for_flip, select_zips_within_metro_for_flip
from src.zillow.similar import similar_zips
from src.zillow.ingest import init_db, ingest_all
from src.zillow.verify_urls import verify_all as verify_urls_all

# ── DB connection ──────────────────────────────────────────────────────────
import threading

_local = threading.local()

def get_conn() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(str(config.DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        _local.conn = conn
    return conn

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(config.DB_PATH)
    get_conn()
    yield
    if _conn:
        _conn.close()

app = FastAPI(title="Fly6 Zillow Pipeline", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Health ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    conn = get_conn()
    series_count = conn.execute("SELECT COUNT(*) FROM series_meta WHERE enabled=1").fetchone()[0]
    fact_count   = conn.execute("SELECT COUNT(*) FROM zillow_facts").fetchone()[0]
    zip_count    = conn.execute("SELECT COUNT(*) FROM zip_cbsa").fetchone()[0]
    return {"status": "ok", "db": "connected",
            "series_count": series_count, "fact_count": fact_count, "zip_cbsa_count": zip_count}

# ── Profile ────────────────────────────────────────────────────────────────
@app.get("/profile/{zip_code}")
def profile(zip_code: str, strategy: str = None):
    conn = get_conn()
    result = build_market_profile(conn, zip_code.zfill(5), strategy)
    if not result:
        raise HTTPException(404, f"No data for ZIP {zip_code}")
    return result

# ── Rank ───────────────────────────────────────────────────────────────────
class RankLTRReq(BaseModel):
    zips: list[str]
    zhvi_max: Optional[float] = None
    yield_min: Optional[float] = None
    zori_yoy_min: Optional[float] = None
    sort_by: str = "gross_yield"
    top_n: int = 10

@app.post("/rank/ltr")
def rank_ltr(req: RankLTRReq):
    return rank_zips_for_ltr(get_conn(), req.zips, req.zhvi_max, req.yield_min, req.zori_yoy_min, req.sort_by, req.top_n)

class RankFlipMetrosReq(BaseModel):
    cbsas: list[str]
    sort_by: str = "sale_to_list"
    top_n: int = 10

@app.post("/rank/flip-metros")
def rank_flip_metros(req: RankFlipMetrosReq):
    return rank_metros_for_flip(get_conn(), req.cbsas, req.sort_by, req.top_n)

class SelectFlipZipsReq(BaseModel):
    cbsa: str
    zips: list[str]
    zhvi_min: Optional[float] = None
    zhvi_max: Optional[float] = None
    require_positive_zhvf: bool = False
    top_n: int = 10

@app.post("/select-flip-zips")
def select_flip_zips(req: SelectFlipZipsReq):
    return select_zips_within_metro_for_flip(get_conn(), req.cbsa, req.zips, req.zhvi_min, req.zhvi_max, req.require_positive_zhvf, req.top_n)

# ── Similar ────────────────────────────────────────────────────────────────
class SimilarReq(BaseModel):
    seed_zip: str
    candidates: list[str]
    k: int = 5

@app.post("/similar-zips")
def similar(req: SimilarReq):
    return similar_zips(get_conn(), req.seed_zip, req.candidates, req.k)

# ── Admin ──────────────────────────────────────────────────────────────────
class RefreshReq(BaseModel):
    mode: str = "both"
    date: Optional[str] = None

@app.post("/admin/refresh")
def admin_refresh(req: RefreshReq, background_tasks: BackgroundTasks):
    background_tasks.add_task(ingest_all, req.mode, req.date)
    return {"status": "started", "mode": req.mode}

@app.get("/admin/verify-urls")
def admin_verify(mode: str = "both"):
    return verify_urls_all(mode)

@app.get("/admin/status")
def admin_status():
    conn = get_conn()
    rows = conn.execute(
        "SELECT run_id, run_date, mode, series_key, status, rows_upserted, error_msg FROM run_log ORDER BY rowid DESC LIMIT 50"
    ).fetchall()
    return [dict(r) for r in rows]
