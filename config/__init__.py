"""
Configuration module for the AI SQL Query Generator.

Provides centralized settings management using Pydantic,
loading values from environment variables and .env files.
"""

from config.settings import settings

__all__ = ["settings"]
