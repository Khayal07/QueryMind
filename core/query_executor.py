"""
SQL query executor.

Safely executes read-only SQL statements against the SQLite database and
returns structured results for the frontend to display.
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from core.schema_builder import get_schema_description
from core.sql_validation import validate_sql_against_database, validate_sql_structure
from database.db_manager import engine
from utils.logger import get_logger

logger = get_logger(__name__)


def execute_query(sql: str) -> dict[str, Any]:
    """
    Execute an SQL statement and return structured results.
    """
    schema = get_schema_description()
    valid, reason = validate_sql_structure(sql, schema)
    if not valid:
        logger.warning("Rejected SQL before execution: %s", reason)
        return {"success": False, "error": reason}

    valid, reason = validate_sql_against_database(sql)
    if not valid:
        logger.warning("SQL validation against database failed: %s", reason)
        return {"success": False, "error": reason}

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(row) for row in result.mappings().all()]

        logger.info("Query executed - %d row(s) returned", len(rows))
        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }
    except SQLAlchemyError as exc:
        logger.error("Query execution failed: %s", exc)
        return {"success": False, "error": str(exc)}
