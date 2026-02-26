from __future__ import annotations

from fastapi import APIRouter

from api.schemas import SimilarZipsRequest
from src.zillow.db import get_conn
from src.zillow.similar import similar_zips

router = APIRouter(tags=["similar"])


@router.post("/similar-zips")
def similar(req: SimilarZipsRequest):
    conn = get_conn()
    return similar_zips(conn, seed_zip=req.seed_zip, candidate_zips=req.candidate_zips, k=req.k)
