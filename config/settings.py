"""
Application settings module.

Uses Pydantic BaseSettings to load configuration from environment
variables and .env files with validation and sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve project root directory (parent of config/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AppSettings(BaseSettings):
    """
    Central configuration for the AI SQL Query Generator.

    Values are loaded from environment variables first, then
    from a .env file at the project root. All fields have
    sensible defaults so the app can run without any config.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Project paths ──────────────────────────────────────
    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    DATABASE_DIR: Path = PROJECT_ROOT / "database"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"

    # ── Database ───────────────────────────────────────────
    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT / 'database' / 'generated.db'}"

    # ── OpenAI / LLM ──────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── Server ─────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # ── Logging ────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"

    @property
    def log_file_path(self) -> Path:
        """Full path to the log file inside the logs directory."""
        return self.LOGS_DIR / self.LOG_FILE

    @property
    def has_openai_key(self) -> bool:
        """Check whether a valid OpenAI API key is configured."""
        return bool(self.OPENAI_API_KEY) and self.OPENAI_API_KEY != "YOUR_OPENAI_API_KEY"


# Singleton instance used across the application
settings = AppSettings()
