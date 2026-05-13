"""
SQL query executor.

Safely executes SQL statements against the SQLite database and
returns structured results for the frontend to display.
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.db_manager import engine
from utils.logger import get_logger

logger = get_logger(__name__)


def execute_query(sql: str) -> dict[str, Any]:
    """
    Execute an SQL statement and return the results.

    Args:
        sql: A valid SQL query string.

    Returns:
        Dictionary with keys:

        - ``success`` (bool): Whether execution succeeded.
        - ``columns`` (list[str]): Column names (on success).
        - ``rows`` (list[dict]): Result rows as dictionaries (on success).
        - ``row_count`` (int): Number of rows returned (on success).
        - ``error`` (str): Error message (on failure).
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(row) for row in result.mappings().all()]

        logger.info("Query executed — %d row(s) returned", len(rows))
        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }
    except SQLAlchemyError as exc:
        logger.error("Query execution failed: %s", exc)
        return {"success": False, "error": str(exc)}
