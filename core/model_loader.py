"""
AI model integration for the SQL Query Generator.

Supports two modes:
1. **OpenAI API** — sends a schema-aware prompt to an OpenAI-compatible
   chat completion endpoint (GPT-4o-mini by default).
2. **Smart fallback** — a keyword-based heuristic that produces basic
   SQL queries when no API key is configured.
"""

import re
from typing import Optional

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# ── OpenAI client (lazy initialisation) ───────────────────

_client = None


def _get_client():
    """Return a cached OpenAI client, or None if no key is set."""
    global _client
    if _client is not None:
        return _client
    if settings.has_openai_key:
        from openai import OpenAI
        _client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE if settings.OPENAI_API_BASE else None,
        )
        logger.info("OpenAI client initialised (model: %s)", settings.OPENAI_MODEL)
    return _client


# ── Public API ────────────────────────────────────────────


def generate_sql(natural_language: str, schema_context: str) -> tuple[str, str]:
    """
    Convert a natural language request into an SQL query.

    Args:
        natural_language: The user's question in plain English.
        schema_context:   A textual description of the database schema.

    Returns:
        A tuple of ``(sql_query, mode)`` where *mode* is either
        ``"openai"`` or ``"fallback"``.
    """
    system_prompt = (
        "You are an expert SQL query generator. Given a database schema "
        "and a natural language question, produce a single valid SQLite "
        "SQL query. Return ONLY the SQL code — no markdown fences, no "
        "explanations, no commentary."
    )
    user_prompt = (
        f"Database schema:\n{schema_context}\n\n"
        f"User question:\n{natural_language}\n\nSQL:"
    )

    client = _get_client()
    if client:
        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=500,
            )
            raw = response.choices[0].message.content.strip()
            sql = _clean_sql_response(raw)
            logger.info("Generated SQL via OpenAI (%s)", settings.OPENAI_MODEL)
            return sql, "openai"
        except Exception as exc:
            logger.warning("OpenAI request failed, falling back: %s", exc)

    # Fallback — keyword-based heuristic
    sql = smart_fallback(natural_language, schema_context)
    return sql, "fallback"


# ── Response cleaning ─────────────────────────────────────


def _clean_sql_response(raw: str) -> str:
    """
    Strip markdown code fences and extra whitespace from an AI response.

    Handles patterns like:
    - ```sql ... ```
    - ```  ... ```
    - Leading/trailing whitespace
    """
    # Remove markdown fences
    cleaned = re.sub(r"^```(?:sql)?\s*\n?", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    return cleaned.strip()


# ── Smart fallback generator ──────────────────────────────


def smart_fallback(natural_language: str, schema_context: str) -> str:
    """
    Produce a best-effort SQL query using keyword heuristics.

    This fallback is used when no OpenAI API key is available.
    It parses the schema context to discover table and column names,
    then matches keywords in the user's request to build a query.

    Args:
        natural_language: The user's question in plain English.
        schema_context:   Schema string in the format produced by
                          :func:`core.sql_generator.build_schema_prompt`.

    Returns:
        A best-effort SQL query string.
    """
    request = natural_language.lower().strip()

    # Parse available tables and columns from schema context
    tables = _parse_schema_tables(schema_context)
    if not tables:
        return "-- No tables found in the database.\nSELECT 1;"

    # If the user typed raw SQL, return it directly
    if request.strip().upper().startswith("SELECT"):
        return natural_language.strip()

    first_table = list(tables.keys())[0]
    first_columns = tables[first_table]

    # Try to match a specific table name from the query
    target_table = first_table
    for table_name in tables:
        if table_name.replace("_", " ") in request or table_name in request:
            target_table = table_name
            break

    target_columns = tables[target_table]

    # ── COUNT queries ──────────────────────────────────
    if any(kw in request for kw in ["how many", "count", "total number"]):
        return f"SELECT COUNT(*) AS total FROM {target_table};"

    # ── DISTINCT queries ───────────────────────────────
    if "unique" in request or "distinct" in request:
        col = _find_column_match(request, target_columns) or target_columns[0]
        return f"SELECT DISTINCT {col} FROM {target_table};"

    # ── AVG / SUM / MIN / MAX ──────────────────────────
    for func, keywords in [
        ("AVG", ["average", "mean", "avg"]),
        ("SUM", ["sum", "total"]),
        ("MAX", ["maximum", "max", "highest", "largest", "most"]),
        ("MIN", ["minimum", "min", "lowest", "smallest", "least"]),
    ]:
        if any(kw in request for kw in keywords):
            col = _find_column_match(request, target_columns) or target_columns[-1]
            return f"SELECT {func}({col}) AS result FROM {target_table};"

    # ── ORDER BY queries ───────────────────────────────
    if any(kw in request for kw in ["sort", "order", "top", "bottom"]):
        col = _find_column_match(request, target_columns) or target_columns[-1]
        direction = "ASC" if any(kw in request for kw in ["ascending", "bottom", "lowest"]) else "DESC"
        limit = "LIMIT 10" if "top" in request or "bottom" in request else ""
        return f"SELECT * FROM {target_table} ORDER BY {col} {direction} {limit};".strip()

    # ── GROUP BY queries ───────────────────────────────
    if "group" in request or "per" in request or "by each" in request:
        col = _find_column_match(request, target_columns) or target_columns[0]
        return f"SELECT {col}, COUNT(*) AS count FROM {target_table} GROUP BY {col};"

    # ── Default: SELECT * ──────────────────────────────
    return f"SELECT * FROM {target_table} LIMIT 50;"


def _parse_schema_tables(schema_context: str) -> dict[str, list[str]]:
    """
    Parse the text schema context into a dict of table → column list.

    Expected format per line::

        table_name: col1 (Type), col2 (Type), ...
    """
    tables: dict[str, list[str]] = {}
    for line in schema_context.strip().split("\n"):
        if ":" not in line:
            continue
        table_part, cols_part = line.split(":", 1)
        table_name = table_part.strip()
        columns = [
            col.strip().split(" ")[0].strip()
            for col in cols_part.split(",")
            if col.strip()
        ]
        if table_name and columns:
            tables[table_name] = columns
    return tables


def _find_column_match(request: str, columns: list[str]) -> Optional[str]:
    """Return the first column whose name appears in the request string."""
    for col in columns:
        if col.replace("_", " ") in request or col in request:
            return col
    return None
