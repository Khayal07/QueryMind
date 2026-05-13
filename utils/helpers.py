"""
Shared helper utilities.

Provides backward-compatible environment loading that delegates
to the centralized ``config.settings`` module.
"""

import re
from typing import Dict


def load_environment() -> Dict[str, str]:
    """
    Load environment variables for the application.

    Returns a dictionary with the keys expected by legacy modules.
    Delegates to ``config.settings`` internally so that all
    configuration flows through a single source of truth.
    """
    from config.settings import settings

    return {
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
        "OPENAI_API_BASE": settings.OPENAI_API_BASE or "",
        "OPENAI_MODEL": settings.OPENAI_MODEL,
        "DATABASE_URL": settings.DATABASE_URL,
    }


def sanitize_name(name: str) -> str:
    """
    Sanitize a string for use as a SQL table or column name.

    - Strips whitespace
    - Converts to lowercase
    - Replaces spaces and special chars with underscores
    - Removes leading digits
    """
    name = name.strip().lower()
    name = re.sub(r"[^\w]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if name and name[0].isdigit():
        name = f"col_{name}"
    return name or "unnamed"
