from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db, SessionLocal
from .routers import articles, daily_report, sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from .services.init_defaults import ensure_default_sources
    db = SessionLocal()
    try:
        ensure_default_sources(db)
    finally:
        db.close()
    from .scheduler import start_scheduler
    start_scheduler()
    yield
    from .scheduler import stop_scheduler
    stop_scheduler()


app = FastAPI(title="NewsDigest API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router, prefix="/api", tags=["articles"])
app.include_router(daily_report.router, prefix="/api", tags=["daily_report"])
app.include_router(sources.router, prefix="/api", tags=["sources"])


@app.get("/api/health")
def health():
    return {"ok": True}
