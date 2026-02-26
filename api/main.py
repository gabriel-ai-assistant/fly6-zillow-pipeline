from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.admin import router as admin_router
from api.routes.profile import router as profile_router
from api.routes.rank import router as rank_router
from api.routes.similar import router as similar_router
from src.zillow.db import close_conn, get_conn
from src.zillow.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    get_conn()
    yield
    close_conn()


app = FastAPI(title="Fly6 Zillow Pipeline API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router)
app.include_router(rank_router)
app.include_router(similar_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    conn = get_conn()
    series_count = conn.execute("SELECT COUNT(*) FROM series_meta").fetchone()[0]
    fact_count = conn.execute("SELECT COUNT(*) FROM zillow_facts").fetchone()[0]
    return {"status": "ok", "db": "connected", "series_count": series_count, "fact_count": fact_count}
