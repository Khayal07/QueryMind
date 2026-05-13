"""
Pydantic request/response schemas for the API layer.

Provides type-safe validation for all API endpoints,
replacing raw dict parameters with structured models.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Request Schemas ────────────────────────────────────────


class GenerateRequest(BaseModel):
    """Request body for the /api/generate endpoint."""

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural language question to convert into SQL.",
        examples=["Show all customers who bought products above 100$"],
    )


class ExecuteRequest(BaseModel):
    """Request body for the /api/execute endpoint."""

    sql: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="SQL query to execute against the database.",
        examples=["SELECT * FROM customers LIMIT 10;"],
    )


# ── Response Schemas ───────────────────────────────────────


class HealthResponse(BaseModel):
    """Response for the /api/health endpoint."""

    status: str = "ok"
    version: str = "1.0.0"
    database_ready: bool = True
    ai_mode: str = "fallback"


class SchemaResponse(BaseModel):
    """Response for the /api/schema endpoint."""

    schema_data: dict[str, dict[str, str]] = Field(
        ..., alias="schema",
        description="Mapping of table names to column name/type pairs.",
    )

    model_config = {"populate_by_name": True}


class TablesResponse(BaseModel):
    """Response for the /api/tables endpoint with enriched table metadata."""

    tables: list[dict[str, Any]] = Field(
        ...,
        description="List of table metadata including name, columns, row count, and sample rows.",
    )


class GenerateResponse(BaseModel):
    """Response for the /api/generate endpoint."""

    sql: str = Field(..., description="The generated SQL query.")
    ai_mode: str = Field("fallback", description="Whether OpenAI or fallback was used.")


class ExecuteResponse(BaseModel):
    """Response for the /api/execute endpoint."""

    columns: list[str] = Field(..., description="Column names of the result set.")
    rows: list[dict[str, Any]] = Field(..., description="Result rows as dictionaries.")
    row_count: int = Field(0, description="Total number of rows returned.")


class ErrorResponse(BaseModel):
    """Standard error response body."""

    detail: str
