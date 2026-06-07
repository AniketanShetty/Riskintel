"""
RiskIntel — Application configuration via Pydantic Settings.

All values are read from environment variables (and .env in development).
Uses Pydantic v2's BaseSettings for validation and type coercion.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Project paths ─────────────────────────────────────────────────────
    # The project root is two levels up from this file:
    #   backend/app/core/config.py -> backend/ -> project root
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

    # ── Application metadata ───────────────────────────────────────────────
    APP_NAME: str = "RiskIntel API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    DEBUG: bool = False

    # ── FastAPI / Uvicorn ──────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
    ]

    # ── Database Configuration ─────────────────────────────────────────────
    # Guaranteed to resolve to backend/riskintel.db
    DB_PATH_ABS: Path = Path(__file__).resolve().parent.parent.parent / "riskintel.db"

    @property
    def DATABASE_URL(self) -> str:
        """Async database URL for SQLAlchemy async engine."""
        return f"sqlite+aiosqlite:///{self.DB_PATH_ABS}"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Synchronous database URL for Alembic migrations."""
        return f"sqlite:///{self.DB_PATH_ABS}"

    # ── Database pool settings ────────────────────────────────────────────
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # ── Storage paths ──────────────────────────────────────────────────────
    MODEL_DIR: Path = Path(os.getenv("MODEL_DIR", str(PROJECT_ROOT / "models")))

    # ── Security ───────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── CORS ───────────────────────────────────────────────────────────────
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


settings = Settings()
