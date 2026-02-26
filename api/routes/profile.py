from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.schemas import MarketProfile
from src.zillow.db import get_conn
from src.zillow.market_profile import build_market_profile

router = APIRouter(tags=["profile"])


@router.get("/profile/{zip}", response_model=MarketProfile)
def get_profile(zip: str, strategy: str = Query(default="both", pattern="^(ltr|flip|both)$")):
    conn = get_conn()
    profile = build_market_profile(conn, zip, strategy=strategy)
    if profile is None:
        raise HTTPException(status_code=404, detail="profile_not_found")
    return profile
