"""
SQL generator orchestrator.

Bridges the schema introspection layer with the AI model loader
to convert natural language questions into executable SQL queries.
"""

from typing import Dict

from core.model_loader import generate_sql
from core.schema_builder import get_schema_description
from utils.logger import get_logger

logger = get_logger(__name__)


def build_schema_prompt(schema: Dict[str, Dict[str, str]]) -> str:
    """
    Serialise a schema dictionary into a text prompt for the AI model.

    Args:
        schema: Mapping of table names to column-name/type pairs.

    Returns:
        Multi-line string describing every table and its columns,
        formatted for consumption by the SQL generation prompt.

    Example output::

        customers: id (Integer), name (String), email (String)
        orders: id (Integer), customer_id (Integer), total (Float)
    """
    parts = []
    for table_name, columns in schema.items():
        column_defs = ", ".join(
            f"{name} ({dtype})" for name, dtype in columns.items()
        )
        parts.append(f"{table_name}: {column_defs}")
    return "\n".join(parts)


def create_sql_from_nl(natural_language: str) -> tuple[str, str]:
    """
    Convert a natural language question into SQL.

    Fetches the current database schema, builds a prompt,
    and passes it to the AI model (or fallback generator).

    Args:
        natural_language: Plain-English question from the user.

    Returns:
        Tuple of ``(sql_query, ai_mode)`` where *ai_mode* is
        ``"openai"`` or ``"fallback"``.
    """
    schema = get_schema_description()
    schema_context = build_schema_prompt(schema)
    sql, mode = generate_sql(natural_language, schema_context)
    logger.info("Generated SQL [%s]: %s", mode, sql[:80])
    return sql, mode
