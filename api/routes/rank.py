from __future__ import annotations

from fastapi import APIRouter

from api.schemas import RankFlipMetrosRequest, RankLTRRequest, SelectFlipZipsRequest
from src.zillow.db import get_conn
from src.zillow.rank import rank_metros_for_flip, rank_zips_for_ltr, select_zips_within_metro_for_flip

router = APIRouter(tags=["rank"])


@router.post("/rank/ltr")
def rank_ltr(req: RankLTRRequest):
    conn = get_conn()
    return rank_zips_for_ltr(
        conn,
        zips=req.zips,
        zhvi_max=req.zhvi_max,
        yield_min=req.yield_min,
        zori_yoy_min=req.zori_yoy_min,
        sort_by=req.sort_by,
        top_n=req.top_n,
    )


@router.post("/rank/flip-metros")
def rank_flip_metros(req: RankFlipMetrosRequest):
    conn = get_conn()
    return rank_metros_for_flip(conn, cbsa_list=req.cbsa_list, sort_by=req.sort_by, top_n=req.top_n)


@router.post("/select-flip-zips")
def select_flip_zips(req: SelectFlipZipsRequest):
    conn = get_conn()
    return select_zips_within_metro_for_flip(
        conn,
        cbsa=req.cbsa,
        zips_in_cbsa=req.zips_in_cbsa,
        zhvi_min=req.zhvi_min,
        zhvi_max=req.zhvi_max,
        require_positive_zhvf=req.require_positive_zhvf,
        top_n=req.top_n,
    )
