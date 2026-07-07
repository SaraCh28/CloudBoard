"""
CloudBoard Backend – Environment & Application Configuration.

All settings are loaded from environment variables (with .env fallback).
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "CloudBoard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development | staging | production

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://cloudboard:cloudboard@localhost:5432/cloudboard"

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-64"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── OAuth (Google) ───────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ── Gemini AI ────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
