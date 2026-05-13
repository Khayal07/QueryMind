"""
Schema builder for the AI SQL Query Generator.

Reads pandas DataFrames produced by the Excel loader, infers
SQLAlchemy column types, creates SQLite tables, and provides
schema introspection utilities used by the API and the prompt
builder.
"""

from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import (
    Table, Column, MetaData, String, Integer,
    Float, Boolean, DateTime, Text, inspect,
)

from database.db_manager import engine
from utils.helpers import sanitize_name
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Type inference ─────────────────────────────────────────

SQLALCHEMY_DTYPE_MAP: dict[str, type] = {
    "object": String,
    "int64": Integer,
    "float64": Float,
    "bool": Boolean,
    "datetime64[ns]": DateTime,
}


def infer_column_type(series: pd.Series) -> type:
    """
    Map a pandas Series dtype to the closest SQLAlchemy column type.

    Args:
        series: A single column from a DataFrame.

    Returns:
        A SQLAlchemy type class (e.g. ``String``, ``Integer``).
    """
    dtype = str(series.dtype)
    if dtype in SQLALCHEMY_DTYPE_MAP:
        return SQLALCHEMY_DTYPE_MAP[dtype]
    if pd.api.types.is_datetime64_any_dtype(series):
        return DateTime
    if pd.api.types.is_integer_dtype(series):
        return Integer
    if pd.api.types.is_float_dtype(series):
        return Float
    if pd.api.types.is_bool_dtype(series):
        return Boolean
    if pd.api.types.is_string_dtype(series):
        return String
    return Text


# ── Database initialisation ───────────────────────────────


def initialize_database_from_excel(excel_path: Path) -> dict[str, dict[str, str]]:
    """
    Build SQLite tables from every sheet in an Excel workbook.

    For each sheet the function:
    1. Sanitises table and column names.
    2. Infers column types from pandas dtypes.
    3. Creates (or replaces) the SQLite table.
    4. Inserts all rows from the DataFrame.

    Args:
        excel_path: Path to the ``.xlsx`` file.

    Returns:
        Schema description mapping table names to column-name/type pairs.
    """
    from core.excel_loader import load_sheets

    logger.info("Building schema from %s", excel_path)
    sheets = load_sheets(excel_path)
    metadata = MetaData()
    schema_description: dict[str, dict[str, str]] = {}

    for sheet_name, df in sheets.items():
        table_name = sanitize_name(sheet_name)

        columns = []
        for col_name in df.columns:
            safe_col = sanitize_name(str(col_name))
            dtype = infer_column_type(df[col_name])
            columns.append(Column(safe_col, dtype, nullable=True))

        Table(table_name, metadata, *columns, extend_existing=True)

        schema_description[table_name] = {
            col.name: col.type.__class__.__name__
            for col in metadata.tables[table_name].columns
        }

        # Rename DataFrame columns to match sanitised names before insert
        df.columns = [col.name for col in metadata.tables[table_name].columns]
        df.to_sql(table_name, con=engine, if_exists="replace", index=False)
        logger.info(
            "Created table '%s': %d columns, %d rows",
            table_name, len(columns), len(df),
        )

    metadata.create_all(engine)
    return schema_description


# ── Schema introspection ──────────────────────────────────


def get_schema_description() -> dict[str, dict[str, str]]:
    """
    Reflect the current database and return a schema description.

    Returns:
        Dictionary mapping each table name to its column-name/type pairs.
    """
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return {
        table_name: {
            col.name: col.type.__class__.__name__
            for col in table.columns
        }
        for table_name, table in metadata.tables.items()
    }


def get_tables_metadata() -> list[dict[str, Any]]:
    """
    Return enriched metadata for every table in the database.

    Each entry includes:
    - ``name``: table name
    - ``columns``: list of ``{name, type}`` dicts
    - ``row_count``: total number of rows
    - ``sample_rows``: first 3 rows as dictionaries

    Returns:
        List of table metadata dictionaries.
    """
    metadata = MetaData()
    metadata.reflect(bind=engine)
    inspector = inspect(engine)
    tables_info: list[dict[str, Any]] = []

    with engine.connect() as conn:
        for table_name, table in metadata.tables.items():
            # Column info
            columns = [
                {"name": col.name, "type": col.type.__class__.__name__}
                for col in table.columns
            ]

            # Row count
            row_count_result = conn.execute(
                table.select().with_only_columns()  # empty select for count
            )
            from sqlalchemy import text
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

            # Sample rows (first 3)
            sample_result = conn.execute(table.select().limit(3))
            sample_rows = [dict(row) for row in sample_result.mappings().all()]

            tables_info.append({
                "name": table_name,
                "columns": columns,
                "row_count": count,
                "sample_rows": sample_rows,
            })

    return tables_info
