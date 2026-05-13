"""
SQL validation helpers for generated and user-provided queries.
"""

from __future__ import annotations

import re
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.db_manager import engine

READ_ONLY_PREFIXES = ("select", "with")
FORBIDDEN_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "truncate",
    "attach",
    "detach",
    "pragma",
)


def quote_identifier(identifier: str) -> str:
    """Quote table or column names for SQLite."""
    return '"' + identifier.replace('"', '""') + '"'


def normalize_sql(sql: str) -> str:
    """Trim SQL and remove a trailing semicolon for validation/explain calls."""
    return sql.strip().rstrip(";").strip()


def is_read_only_sql(sql: str) -> bool:
    """Allow only read-only SELECT / CTE queries."""
    normalized = normalize_sql(sql).lower()
    if not normalized.startswith(READ_ONLY_PREFIXES):
        return False
    return not any(re.search(rf"\b{keyword}\b", normalized) for keyword in FORBIDDEN_KEYWORDS)


def extract_referenced_tables(sql: str) -> list[str]:
    """Return table names referenced after FROM / JOIN clauses."""
    matches = re.finditer(
        r'(?i)\b(?:from|join)\s+("([^"]+)"|[A-Za-z0-9_\-\u0080-\uffff]+)',
        sql,
    )
    tables: list[str] = []
    for match in matches:
        raw_table = match.group(2) or match.group(1)
        table_name = raw_table.strip('"')
        if table_name:
            tables.append(table_name)
    return tables


def validate_sql_structure(sql: str, schema: dict[str, dict[str, str]]) -> tuple[bool, str]:
    """Validate that SQL is read-only and only references known tables."""
    normalized = normalize_sql(sql)
    if not normalized:
        return False, "SQL is empty."

    if not is_read_only_sql(normalized):
        return False, "Only read-only SELECT queries are allowed."

    if normalized.count(";") > 0 and ";" in normalized:
        return False, "Only a single SQL statement is allowed."

    known_tables = set(schema.keys())
    referenced_tables = extract_referenced_tables(normalized)
    unknown_tables = sorted({table for table in referenced_tables if table not in known_tables})
    if unknown_tables:
        return False, f"SQL references unknown tables: {', '.join(unknown_tables)}."

    return True, "ok"


def validate_sql_against_database(sql: str) -> tuple[bool, str]:
    """Use SQLite query planning to validate syntax before execution."""
    normalized = normalize_sql(sql)
    if not normalized:
        return False, "SQL is empty."

    if not is_read_only_sql(normalized):
        return False, "Only read-only SELECT queries are allowed."

    try:
        with engine.connect() as conn:
            conn.execute(text(f"EXPLAIN QUERY PLAN {normalized}"))
        return True, "ok"
    except SQLAlchemyError as exc:
        return False, str(exc)


def simple_identifier_list(columns: Iterable[str]) -> str:
    """Return a comma-separated list of quoted identifiers."""
    return ", ".join(quote_identifier(column) for column in columns)
