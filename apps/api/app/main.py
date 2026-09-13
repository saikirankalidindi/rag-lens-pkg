"""
RAGLens API — main application factory.

All routers are registered here. Keep this file thin.
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup / shutdown logic."""
    logger.info("RAGLens API starting up")

    # Seed demo data on first boot (no-op if already seeded)
    try:
        from app.database.connection import AsyncSessionLocal
        from app.seed import run_seed
        async with AsyncSessionLocal() as session:
            await run_seed(session)
    except Exception as exc:
        # Never crash startup due to a seed failure
        logger.warning("Seed failed (non-fatal): %s", exc)

    yield
    logger.info("RAGLens API shutting down")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="RAGLens API",
        description=(
            "Observability and debugging platform for RAG pipelines. "
            "Chrome DevTools for RAG."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request timing middleware ──────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        return response

    # ── Health endpoint ────────────────────────────────────────────────────
    @app.get("/health", tags=["meta"], summary="Health check")
    async def health():
        return {"status": "ok", "version": app.version}

    # ── Routers ────────────────────────────────────────────────────────────
    from app.api import auth, projects, traces, ingestion, api_keys

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(projects.router, prefix="/projects", tags=["projects"])
    app.include_router(traces.router, tags=["traces"])
    app.include_router(ingestion.router, prefix="/v1", tags=["ingestion"])
    app.include_router(api_keys.router, tags=["api-keys"])

    return app


app = create_app()
