"""
Centralized application configuration.

Uses pydantic-settings for environment variable management.
Supports SQLite (default) and PostgreSQL via DATABASE_URL.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "Darwix AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./darwix.db"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # ── File Storage ─────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ── STT (Speech-to-Text) ────────────────────────────────────────────
    STT_PROVIDER: Literal["whisper"] = "whisper"
    WHISPER_MODEL_SIZE: str = "base"

    # ── TTS (Text-to-Speech) ────────────────────────────────────────────
    TTS_PROVIDER: Literal["gtts", "pyttsx3"] = "gtts"

    # ── Sentiment Analysis ───────────────────────────────────────────────
    SENTIMENT_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"
    SENTIMENT_ENABLED: bool = True

    # ── Coachable Moment Detection ───────────────────────────────────────
    COACHABLE_CONFIDENCE_THRESHOLD: float = 0.5

    # ── Celery / Task Queue (future) ─────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── Derived helpers ──────────────────────────────────────────────────
    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def output_path(self) -> Path:
        p = Path(self.OUTPUT_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    return Settings()
