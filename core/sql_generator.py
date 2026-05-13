"""
SQL generator orchestrator.

Builds a rich schema-aware prompt context and delegates SQL generation
to the model loader or deterministic fallback pipeline.
"""

from __future__ import annotations

from typing import Any

from core.model_loader import generate_sql
from core.schema_builder import get_schema_description, get_tables_metadata
from utils.logger import get_logger

logger = get_logger(__name__)


def _safe_log_text(value: str) -> str:
    return value.encode("unicode_escape").decode("ascii")


def _table_preference_score(table_name: str) -> tuple[int, int]:
    punctuation_penalty = sum(1 for char in table_name if not (char.isalnum() or char == "_"))
    underscore_bonus = table_name.count("_")
    return (-punctuation_penalty, underscore_bonus)


def _normalize_signature_name(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value.lower())


def _deduplicate_schema_view(
    schema: dict[str, dict[str, str]],
    tables_metadata: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, str]], list[dict[str, Any]]]:
    grouped: dict[tuple[tuple[str, str], ...], list[str]] = {}
    for table_name, columns in schema.items():
        signature = tuple(
            (_normalize_signature_name(column_name), dtype)
            for column_name, dtype in columns.items()
        )
        grouped.setdefault(signature, []).append(table_name)

    canonical_names: dict[str, str] = {}
    for names in grouped.values():
        preferred = sorted(names, key=_table_preference_score, reverse=True)[0]
        for name in names:
            canonical_names[name] = preferred

    deduped_schema = {
        canonical_names[table_name]: columns
        for table_name, columns in schema.items()
        if canonical_names[table_name] == table_name
    }
    deduped_metadata = [
        table for table in tables_metadata if canonical_names.get(table["name"], table["name"]) == table["name"]
    ]
    return deduped_schema, deduped_metadata


def _describe_column(column_name: str, dtype: str) -> str:
    lowered = column_name.lower()
    notes: list[str] = []

    if lowered == "id":
        notes.append("primary identifier candidate")
    if lowered.endswith("_id"):
        notes.append("foreign-key-like reference candidate")
    if "date" in lowered or "tarix" in lowered:
        notes.append("date/time field")
    if any(token in lowered for token in ("name", "title", "ad")):
        notes.append("label/text field")
    if any(token in lowered for token in ("amount", "total", "sum", "value", "price", "vergisi", "məbləği")):
        notes.append("numeric measure candidate")

    notes_text = f" - {', '.join(notes)}" if notes else ""
    return f"- {column_name}: {dtype}{notes_text}"


def build_schema_context(
    schema: dict[str, dict[str, str]],
    tables_metadata: list[dict[str, Any]],
) -> str:
    """
    Serialise schema and metadata into a rich prompt context for SQL generation.
    """
    if not schema:
        return "No tables are currently available."

    metadata_by_name = {table["name"]: table for table in tables_metadata}
    sections: list[str] = []

    for table_name, columns in schema.items():
        table_meta = metadata_by_name.get(table_name, {})
        row_count = table_meta.get("row_count", "unknown")
        sections.append(f"Table: {table_name}")
        sections.append(f"Row count: {row_count}")
        sections.append("Columns:")
        sections.extend(_describe_column(column_name, dtype) for column_name, dtype in columns.items())

        sample_rows = table_meta.get("sample_rows") or []
        if sample_rows:
            preview = sample_rows[:2]
            sections.append(f"Sample rows: {preview}")

        sections.append("")

    return "\n".join(sections).strip()


def create_sql_from_nl(natural_language: str) -> tuple[str, str]:
    """
    Convert a natural language question into SQL using current schema context.
    """
    schema = get_schema_description()
    tables_metadata = get_tables_metadata()
    schema, tables_metadata = _deduplicate_schema_view(schema, tables_metadata)
    schema_context = build_schema_context(schema, tables_metadata)
    sql, mode = generate_sql(natural_language, schema, schema_context)
    logger.info("Generated SQL [%s]: %s", mode, _safe_log_text(sql[:200]))
    return sql, mode
