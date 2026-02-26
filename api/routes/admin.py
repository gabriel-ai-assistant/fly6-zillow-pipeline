from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Query

from api.schemas import AdminStatusResponse, RefreshRequest, VerifyUrlsResponse
from src.zillow.db import get_conn
from src.zillow.init_db import init_db
from src.zillow.refresh import run_refresh
from src.zillow.verify_urls import verify_all
from src.zillow.zip_cbsa import build_zip_to_cbsa

router = APIRouter(tags=["admin"])


def _refresh_task(mode: str, run_date: str | None) -> None:
    init_db()
    run_refresh(mode, run_date)


@router.post("/admin/refresh")
def refresh(req: RefreshRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(_refresh_task, req.mode, req.run_date)
    return {"status": "started", "mode": req.mode, "run_date": req.run_date}


@router.post("/admin/build-zip-cbsa")
def build_zip_cbsa(background_tasks: BackgroundTasks):
    background_tasks.add_task(build_zip_to_cbsa)
    return {"status": "started", "action": "build-zip-cbsa"}


@router.get("/admin/verify-urls", response_model=VerifyUrlsResponse)
def verify_urls(mode: str = Query(default="both", pattern="^(ltr|flip|both)$")):
    return verify_all(mode=mode)


@router.get("/admin/status", response_model=AdminStatusResponse)
def admin_status(limit: int = Query(default=20, ge=1, le=200)):
    conn = get_conn()
    cur = conn.execute(
        "SELECT id, ts, action, status, details FROM run_log ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    return {"entries": rows}
