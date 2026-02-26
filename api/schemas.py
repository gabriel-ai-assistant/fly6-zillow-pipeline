from __future__ import annotations

from pydantic import BaseModel, Field


class LTRMetrics(BaseModel):
    zhvi: float | None = None
    zori: float | None = None
    gross_yield: float | None = None
    zhvi_yoy: float | None = None
    zori_yoy: float | None = None
    data_available: bool = False


class FlipMetrics(BaseModel):
    cbsa: str | None = None
    metro_name: str | None = None
    sale_to_list: float | None = None
    market_heat: float | None = None
    price_cut_pct: float | None = None
    days_to_pending: float | None = None
    inventory: float | None = None
    data_available: bool = False


class MarketProfile(BaseModel):
    zip: str
    as_of: str | None = None
    ltr: LTRMetrics | None = None
    flip: FlipMetrics | None = None
    flip_null_reason: str | None = None


class RankLTRRequest(BaseModel):
    zips: list[str]
    zhvi_max: float | None = None
    yield_min: float | None = Field(default=None, alias="yield_min")
    zori_yoy_min: float | None = None
    sort_by: str = "gross_yield"
    top_n: int = 10


class RankFlipMetrosRequest(BaseModel):
    cbsa_list: list[str]
    sort_by: str = "sale_to_list"
    top_n: int = 10


class SelectFlipZipsRequest(BaseModel):
    cbsa: str
    zips_in_cbsa: list[str]
    zhvi_min: float | None = None
    zhvi_max: float | None = None
    require_positive_zhvf: bool = False
    top_n: int = 10


class SimilarZipsRequest(BaseModel):
    seed_zip: str
    candidate_zips: list[str]
    k: int = 5


class RefreshRequest(BaseModel):
    mode: str = "both"
    run_date: str | None = None


class VerifyUrlsResponse(BaseModel):
    mode: str
    date: str
    checks: list[dict]
    required_failed: list[str]
    ok: bool


class AdminStatusResponse(BaseModel):
    entries: list[dict]
