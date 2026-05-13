"""
AI model integration for the SQL Query Generator.

Supports two modes:
1. OpenAI API with a schema-aware prompt.
2. Schema-aware deterministic fallback when no valid API key is configured.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from config.settings import settings
from core.sql_validation import quote_identifier, simple_identifier_list, validate_sql_structure
from utils.logger import get_logger

logger = get_logger(__name__)

_client = None


def _safe_log_text(value: str) -> str:
    """Make debug logs safe for Windows consoles with limited encodings."""
    return value.encode("unicode_escape").decode("ascii")


@dataclass(frozen=True)
class Relationship:
    left_table: str
    left_column: str
    right_table: str
    right_column: str


def _get_client():
    """Return a cached OpenAI client, or None if no valid key is set."""
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
    else:
        logger.info("OpenAI client not initialised; using schema-aware fallback mode.")
    return _client


def generate_sql(
    natural_language: str,
    schema: dict[str, dict[str, str]],
    schema_context: str,
) -> tuple[str, str]:
    """
    Convert a natural language request into an SQL query.

    Returns ``(sql_query, mode)`` where mode is ``openai`` or ``fallback``.
    """
    system_prompt = (
        "You are an expert SQLite analyst. Convert the user question into one valid "
        "SQLite SELECT query using only the provided schema. Use exact table and column "
        "names from the schema. Prefer explicit column lists over SELECT *. Add JOINs "
        "when the question spans multiple tables. Use double quotes around identifiers "
        "when needed. Return only SQL with no markdown and no explanation."
    )
    user_prompt = (
        "Database schema and context:\n"
        f"{schema_context}\n\n"
        "Generation rules:\n"
        "- Use only available tables and columns.\n"
        "- If the question requests filtering, sorting, grouping, totals, or counts, express that in SQL.\n"
        "- If no row limit is requested, do not invent a generic fallback query.\n"
        "- If a join is needed, infer it from matching keys such as id / *_id.\n\n"
        f"User question:\n{natural_language}\n\n"
        "SQL:"
    )

    logger.info("Schema context for SQL generation:\n%s", _safe_log_text(schema_context))
    logger.info(
        "Constructed SQL prompt:\nSYSTEM:\n%s\n\nUSER:\n%s",
        _safe_log_text(system_prompt),
        _safe_log_text(user_prompt),
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
                temperature=0.05,
                max_tokens=500,
            )
            raw = (response.choices[0].message.content or "").strip()
            logger.info("Raw SQL model output:\n%s", _safe_log_text(raw))
            sql = _clean_sql_response(raw)
            valid, reason = validate_sql_structure(sql, schema)
            if valid:
                logger.info("Generated SQL via OpenAI (%s)", settings.OPENAI_MODEL)
                return sql, "openai"

            logger.warning("Model output failed validation: %s", reason)
        except Exception as exc:
            logger.warning("OpenAI request failed, falling back: %s", exc)

    sql = smart_schema_fallback(natural_language, schema)
    logger.info("Raw SQL model output:\n%s", _safe_log_text(sql))
    return sql, "fallback"


def _clean_sql_response(raw: str) -> str:
    """Strip markdown code fences and extra whitespace from an AI response."""
    cleaned = re.sub(r"^```(?:sql)?\s*\n?", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    return cleaned.strip()


def smart_schema_fallback(
    natural_language: str,
    schema: dict[str, dict[str, str]],
) -> str:
    """
    Build a schema-aware SQL query without using a language model.

    This fallback is deterministic and never returns a hardcoded generic table query.
    """
    request = natural_language.strip()
    request_normalized = _normalize_text(request)

    if request.upper().startswith("SELECT"):
        valid, _ = validate_sql_structure(request, schema)
        if valid:
            return request

    if not schema:
        return "SELECT 1 AS no_data_available"

    relationships = _infer_relationships(schema)
    matched_tables = _rank_tables(request_normalized, schema)
    target_tables = [table for table, score in matched_tables if score > 0][:2]
    if not target_tables:
        target_tables = [next(iter(schema.keys()))]

    matched_columns = _match_columns(request_normalized, schema)
    if (
        len(target_tables) >= 2
        and _tables_look_equivalent(schema, target_tables[0], target_tables[1])
    ):
        target_tables = target_tables[:1]
    elif not _question_requires_multiple_tables(request_normalized, target_tables, matched_columns):
        target_tables = target_tables[:1]

    filter_specs = _extract_filters(request)
    aggregate = _detect_aggregate(request_normalized)
    wants_count = any(phrase in request_normalized for phrase in ("how many", "count", "number of"))
    wants_distinct = "distinct" in request_normalized or "unique" in request_normalized
    wants_top = "top" in request_normalized or "highest" in request_normalized or "largest" in request_normalized
    wants_bottom = "bottom" in request_normalized or "lowest" in request_normalized or "smallest" in request_normalized

    if len(target_tables) > 1:
        join_sql, aliases = _build_join_clause(target_tables, schema, relationships)
    else:
        aliases = {target_tables[0]: "t1"}
        join_sql = f"FROM {quote_identifier(target_tables[0])} AS t1"

    selected_refs = _select_columns_for_query(
        request_normalized=request_normalized,
        schema=schema,
        target_tables=target_tables,
        aliases=aliases,
        matched_columns=matched_columns,
        aggregate=aggregate,
        wants_count=wants_count,
        wants_distinct=wants_distinct,
    )

    where_clauses = _build_where_clauses(filter_specs, schema, target_tables, aliases, matched_columns)
    order_clause = _build_order_clause(
        request_normalized,
        schema,
        target_tables,
        aliases,
        matched_columns,
        wants_top,
        wants_bottom,
    )
    group_by = _build_group_by_clause(selected_refs, aggregate, wants_count, wants_distinct)
    limit_clause = _build_limit_clause(request_normalized, wants_top, wants_bottom)

    sql_parts = [f"SELECT {'DISTINCT ' if wants_distinct and not wants_count else ''}{selected_refs}", join_sql]
    if where_clauses:
        sql_parts.append("WHERE " + " AND ".join(where_clauses))
    if group_by:
        sql_parts.append(group_by)
    if order_clause:
        sql_parts.append(order_clause)
    if limit_clause:
        sql_parts.append(limit_clause)

    sql = "\n".join(sql_parts) + ";"
    valid, reason = validate_sql_structure(sql, schema)
    if valid:
        return sql

    logger.warning("Fallback SQL failed validation, using deterministic table projection: %s", reason)
    first_table = target_tables[0]
    projected_columns = list(schema[first_table].keys())[: min(5, len(schema[first_table]))]
    return (
        f"SELECT {simple_identifier_list(projected_columns)}\n"
        f"FROM {quote_identifier(first_table)}\n"
        "LIMIT 50;"
    )


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9_ ]+", " ", value.lower()).strip()


def _tokenize_identifier(identifier: str) -> set[str]:
    normalized = _normalize_text(identifier.replace("_", " "))
    pieces = {piece for piece in normalized.split() if piece}
    if normalized:
        pieces.add(normalized.replace(" ", "_"))
        pieces.add(normalized.replace(" ", ""))
    return pieces


def _normalized_column_signature(columns: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (_normalize_text(column_name).replace(" ", "_"), dtype)
        for column_name, dtype in columns.items()
    )


def _tables_look_equivalent(
    schema: dict[str, dict[str, str]],
    left_table: str,
    right_table: str,
) -> bool:
    return _normalized_column_signature(schema[left_table]) == _normalized_column_signature(schema[right_table])


def _rank_tables(
    request_normalized: str,
    schema: dict[str, dict[str, str]],
) -> list[tuple[str, int]]:
    ranked: list[tuple[str, int]] = []
    request_tokens = set(request_normalized.split())

    for table_name, columns in schema.items():
        score = 0
        table_tokens = _tokenize_identifier(table_name)
        score += sum(5 for token in table_tokens if token in request_normalized or token in request_tokens)

        for column_name in columns:
            column_tokens = _tokenize_identifier(column_name)
            score += sum(2 for token in column_tokens if token in request_normalized or token in request_tokens)

        ranked.append((table_name, score))

    return sorted(ranked, key=lambda item: item[1], reverse=True)


def _question_requires_multiple_tables(
    request_normalized: str,
    target_tables: list[str],
    matched_columns: dict[str, list[str]],
) -> bool:
    if len(target_tables) < 2:
        return False

    explicit_join_keywords = (" join ", " combine ", " compare ", " versus ", " vs ", " between ")
    if any(keyword in f" {request_normalized} " for keyword in explicit_join_keywords):
        return True

    explicitly_mentioned_tables = 0
    for table_name in target_tables:
        if any(token in request_normalized for token in _tokenize_identifier(table_name)):
            explicitly_mentioned_tables += 1
    if explicitly_mentioned_tables >= 2:
        return True

    return False


def _match_columns(
    request_normalized: str,
    schema: dict[str, dict[str, str]],
) -> dict[str, list[str]]:
    matches: dict[str, list[str]] = {}
    for table_name, columns in schema.items():
        for column_name in columns:
            if any(token in request_normalized for token in _tokenize_identifier(column_name)):
                matches.setdefault(table_name, []).append(column_name)
    return matches


def _infer_relationships(schema: dict[str, dict[str, str]]) -> list[Relationship]:
    relationships: list[Relationship] = []
    for table_name, columns in schema.items():
        for column_name in columns:
            if not column_name.endswith("_id"):
                continue
            target_base = column_name[:-3]
            for other_table, other_columns in schema.items():
                if other_table == table_name or "id" not in other_columns:
                    continue
                other_tokens = _tokenize_identifier(other_table)
                if target_base in other_tokens or target_base.rstrip("s") in other_tokens:
                    relationships.append(
                        Relationship(
                            left_table=table_name,
                            left_column=column_name,
                            right_table=other_table,
                            right_column="id",
                        )
                    )
    return relationships


def _build_join_clause(
    target_tables: list[str],
    schema: dict[str, dict[str, str]],
    relationships: list[Relationship],
) -> tuple[str, dict[str, str]]:
    aliases = {table: f"t{index + 1}" for index, table in enumerate(target_tables)}
    base_table = target_tables[0]
    parts = [f"FROM {quote_identifier(base_table)} AS {aliases[base_table]}"]

    for table in target_tables[1:]:
        relationship = _find_relationship(base_table, table, relationships)
        if relationship:
            left_alias = aliases[relationship.left_table]
            right_alias = aliases[relationship.right_table]
            parts.append(
                "JOIN "
                f"{quote_identifier(table)} AS {aliases[table]} "
                f"ON {left_alias}.{quote_identifier(relationship.left_column)} = "
                f"{right_alias}.{quote_identifier(relationship.right_column)}"
            )
            continue

        common_column = _find_common_column(schema[base_table], schema[table])
        if common_column:
            parts.append(
                "JOIN "
                f"{quote_identifier(table)} AS {aliases[table]} "
                f"ON {aliases[base_table]}.{quote_identifier(common_column)} = "
                f"{aliases[table]}.{quote_identifier(common_column)}"
            )
            continue

        parts.append(f"CROSS JOIN {quote_identifier(table)} AS {aliases[table]}")

    return "\n".join(parts), aliases


def _find_relationship(left_table: str, right_table: str, relationships: list[Relationship]) -> Optional[Relationship]:
    for relationship in relationships:
        if relationship.left_table == left_table and relationship.right_table == right_table:
            return relationship
        if relationship.left_table == right_table and relationship.right_table == left_table:
            return Relationship(
                left_table=left_table,
                left_column=relationship.right_column,
                right_table=right_table,
                right_column=relationship.left_column,
            )
    return None


def _find_common_column(left_columns: dict[str, str], right_columns: dict[str, str]) -> Optional[str]:
    shared = set(left_columns).intersection(right_columns)
    for preferred in ("id", "date", "name"):
        if preferred in shared:
            return preferred
    return next(iter(shared), None)


def _extract_filters(request: str) -> list[tuple[str, float, str]]:
    patterns = [
        (r"([A-Za-z0-9_ ]+?)\s+(?:above|greater than|more than|over)\s+(-?\d+(?:\.\d+)?)", ">"),
        (r"([A-Za-z0-9_ ]+?)\s+(?:below|less than|under)\s+(-?\d+(?:\.\d+)?)", "<"),
        (r"([A-Za-z0-9_ ]+?)\s+(?:equal to|equals?)\s+(-?\d+(?:\.\d+)?)", "="),
    ]
    filters: list[tuple[str, float, str]] = []
    for pattern, operator in patterns:
        for match in re.finditer(pattern, request, flags=re.IGNORECASE):
            column_hint = _normalize_text(match.group(1))
            value = float(match.group(2))
            filters.append((column_hint, value, operator))
    return filters


def _detect_aggregate(request_normalized: str) -> Optional[str]:
    aggregate_map = {
        "average": "AVG",
        "avg": "AVG",
        "mean": "AVG",
        "sum": "SUM",
        "total": "SUM",
        "maximum": "MAX",
        "max": "MAX",
        "minimum": "MIN",
        "min": "MIN",
    }
    for keyword, aggregate in aggregate_map.items():
        if keyword in request_normalized:
            return aggregate
    return None


def _select_columns_for_query(
    *,
    request_normalized: str,
    schema: dict[str, dict[str, str]],
    target_tables: list[str],
    aliases: dict[str, str],
    matched_columns: dict[str, list[str]],
    aggregate: Optional[str],
    wants_count: bool,
    wants_distinct: bool,
) -> str:
    projected_refs: list[str] = []

    if wants_count:
        return "COUNT(*) AS total_count"

    preferred_dimension_tokens = ("name", "title", "type", "status", "date", "tarix", "ad")

    for table in target_tables:
        for column in matched_columns.get(table, []):
            projected_refs.append(f'{aliases[table]}.{quote_identifier(column)}')

    if not projected_refs:
        for table in target_tables:
            for column_name in schema[table]:
                token_set = _tokenize_identifier(column_name)
                if any(token in token_set for token in preferred_dimension_tokens):
                    projected_refs.append(f'{aliases[table]}.{quote_identifier(column_name)}')
                    break

    aggregate_target: Optional[str] = None
    if aggregate:
        for table in target_tables:
            for column_name, dtype in schema[table].items():
                if dtype.upper() in {"INTEGER", "FLOAT", "NUMERIC", "REAL"}:
                    if table in matched_columns and column_name in matched_columns[table]:
                        aggregate_target = f'{aliases[table]}.{quote_identifier(column_name)}'
                        break
            if aggregate_target:
                break

        if not aggregate_target:
            for table in target_tables:
                for column_name, dtype in schema[table].items():
                    if dtype.upper() in {"INTEGER", "FLOAT", "NUMERIC", "REAL"}:
                        aggregate_target = f'{aliases[table]}.{quote_identifier(column_name)}'
                        break
                if aggregate_target:
                    break

    if aggregate and aggregate_target:
        dimension = projected_refs[0] if projected_refs else None
        if dimension:
            return f"{dimension}, {aggregate}({aggregate_target}) AS aggregated_value"
        return f"{aggregate}({aggregate_target}) AS aggregated_value"

    if wants_distinct and projected_refs:
        return ", ".join(dict.fromkeys(projected_refs))

    if projected_refs:
        return ", ".join(dict.fromkeys(projected_refs[:6]))

    first_table = target_tables[0]
    fallback_columns = list(schema[first_table].keys())[: min(5, len(schema[first_table]))]
    return ", ".join(f'{aliases[first_table]}.{quote_identifier(column)}' for column in fallback_columns)


def _build_where_clauses(
    filter_specs: list[tuple[str, float, str]],
    schema: dict[str, dict[str, str]],
    target_tables: list[str],
    aliases: dict[str, str],
    matched_columns: dict[str, list[str]],
) -> list[str]:
    clauses: list[str] = []
    for column_hint, value, operator in filter_specs:
        resolved = _resolve_column_hint(column_hint, schema, target_tables, matched_columns)
        if not resolved:
            continue
        table_name, column_name = resolved
        numeric_value = int(value) if value.is_integer() else value
        clauses.append(f"{aliases[table_name]}.{quote_identifier(column_name)} {operator} {numeric_value}")
    return clauses


def _resolve_column_hint(
    column_hint: str,
    schema: dict[str, dict[str, str]],
    target_tables: list[str],
    matched_columns: dict[str, list[str]],
) -> Optional[tuple[str, str]]:
    for table in target_tables:
        for column_name in matched_columns.get(table, []):
            if any(token in column_hint for token in _tokenize_identifier(column_name)):
                return table, column_name

    for table in target_tables:
        for column_name in schema[table]:
            if any(token in column_hint for token in _tokenize_identifier(column_name)):
                return table, column_name

    return None


def _build_order_clause(
    request_normalized: str,
    schema: dict[str, dict[str, str]],
    target_tables: list[str],
    aliases: dict[str, str],
    matched_columns: dict[str, list[str]],
    wants_top: bool,
    wants_bottom: bool,
) -> str:
    if not any(keyword in request_normalized for keyword in ("top", "bottom", "highest", "lowest", "latest", "earliest", "sort", "order")):
        return ""

    direction = "DESC"
    if wants_bottom or "ascending" in request_normalized or "earliest" in request_normalized:
        direction = "ASC"

    for table in target_tables:
        for column_name in matched_columns.get(table, []):
            return f"ORDER BY {aliases[table]}.{quote_identifier(column_name)} {direction}"

    for table in target_tables:
        for column_name in schema[table]:
            if schema[table][column_name].upper() in {"INTEGER", "FLOAT", "NUMERIC", "REAL", "DATETIME", "DATE"}:
                return f"ORDER BY {aliases[table]}.{quote_identifier(column_name)} {direction}"

    return ""


def _build_group_by_clause(
    selected_refs: str,
    aggregate: Optional[str],
    wants_count: bool,
    wants_distinct: bool,
) -> str:
    if wants_count or wants_distinct:
        return ""

    if not aggregate:
        return ""

    first_selected = selected_refs.split(",")[0].strip()
    if " AS aggregated_value" in selected_refs and not first_selected.startswith(("SUM(", "AVG(", "MIN(", "MAX(")):
        return f"GROUP BY {first_selected}"

    return ""


def _build_limit_clause(request_normalized: str, wants_top: bool, wants_bottom: bool) -> str:
    explicit_limit = re.search(r"\b(?:limit|top)\s+(\d+)\b", request_normalized)
    if explicit_limit:
        return f"LIMIT {explicit_limit.group(1)}"
    if wants_top or wants_bottom:
        return "LIMIT 10"
    return ""
