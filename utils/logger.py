"""
Logging utility for the AI SQL Query Generator.

Provides a configured logger with both console and file output.
Log files are written to the ``logs/`` directory with automatic
rotation to prevent unbounded growth.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Resolve logs directory relative to project root
_LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOGS_DIR.mkdir(exist_ok=True)

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB per log file
_BACKUP_COUNT = 3


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return a named logger with console and rotating-file handlers.

    Args:
        name:  Logger name (typically ``__name__``).
        level: Minimum log level (default ``INFO``).

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Console handler — writes to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler — rotating log files in logs/
    try:
        file_handler = RotatingFileHandler(
            _LOGS_DIR / "app.log",
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        logger.warning("Could not create log file — logging to console only.")

    return logger
