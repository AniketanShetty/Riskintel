"""
RiskIntel — FastAPI application factory.

Usage:
    uvicorn app.main:app --reload

Or via Docker:
    docker run -p 8000:8000 riskintel-backend
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.responses import ErrorResponse, ErrorDetail

# ── Configure root logger ────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger(__name__)


# ── Application lifespan (startup / shutdown) ────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.

    Startup:
        - Log application info.
        - (Future) Initialize database connection pool.
        - (Future) Load ML models into memory.

    Shutdown:
        - Dispose of the async database engine.
        - (Future) Release ML model references.
    """
    logger.info(
        "Starting %s v%s — environment: %s",
        settings.APP_NAME,
        settings.APP_VERSION,
        "development" if settings.DEBUG else "production",
    )

    # Startup tasks -----------------------------------------------------------
    try:
        from app.db.session import engine
    except Exception as exc:  # SQLAlchemy/aiosqlite not installed — assess route does not need DB
        logger.warning("Database engine not available at startup: %s", exc)
        engine = None

    # Verify database connectivity at startup (non-blocking warn)
    if engine is not None:
        try:
            async with engine.connect() as conn:
                from sqlalchemy import text

                await conn.execute(text("SELECT 1"))
            logger.info("Database connection established.")
        except Exception as exc:
            logger.warning("Database not reachable at startup: %s", exc)

    yield  # Application runs here

    # Shutdown tasks ----------------------------------------------------------
    if engine is not None:
        logger.info("Shutting down — disposing database engine.")
        await engine.dispose()


# ── FastAPI application instance ──────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="RiskIntel — AI-powered credit assessment and borrower profiling platform.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)


# ── CORS middleware ────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# ── Exception handlers ────────────────────────────────────────────────────


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    has_missing = False
    has_type = False
    
    for err in exc.errors():
        err_type = err.get("type", "")
        if err_type == "missing":
            has_missing = True
        elif "type" in err_type or "json" in err_type:
            has_type = True
            
        field_loc = err.get("loc", [])
        field_name = str(field_loc[-1]) if len(field_loc) > 0 else "unknown"
        
        details.append({
            "field": field_name,
            "value": err.get("input", None),
            "rule": err_type,
            "message": err.get("msg", "Validation failed")
        })

    if has_missing:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error": {"code": "MISSING_REQUIRED_FIELD", "message": "A required field is missing from the request body."}}
        )

    return JSONResponse(
        status_code=400,
        content={"status": "error", "error": {"code": "VALIDATION_ERROR", "message": "One or more input fields failed validation.", "details": details}}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "error": {"code": "HTTP_ERROR", "message": str(exc.detail)}}
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred during processing."}}
    )


# ── Register routers ──────────────────────────────────────────────────────

from app.api.health import router as health_router
from app.api.assess import router as assess_router
from app.api.reports import router as reports_router

app.include_router(health_router, prefix="/health")
app.include_router(assess_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
