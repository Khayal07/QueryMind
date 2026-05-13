"""
FastAPI route definitions for the AI SQL Query Generator.

Endpoints:
    GET  /api/health   — Service health check.
    GET  /api/schema   — Return the inferred database schema.
    GET  /api/tables   — Return enriched table metadata.
    POST /api/generate — Convert natural language to SQL.
    POST /api/execute  — Execute a SQL query and return results.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api.schemas import (
    GenerateRequest, ExecuteRequest,
    HealthResponse, GenerateResponse, ExecuteResponse,
)
from config.settings import settings
from core.sql_generator import create_sql_from_nl
from core.schema_builder import get_schema_description, get_tables_metadata
from core.query_executor import execute_query
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ── Health ─────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health and readiness check."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        database_ready=True,
        ai_mode="openai" if settings.has_openai_key else "fallback",
    )


# ── Schema ─────────────────────────────────────────────────


@router.get("/schema")
async def fetch_schema():
    """Return the current database schema (table → column/type map)."""
    schema = get_schema_description()
    return {"schema": schema}


@router.get("/tables")
async def fetch_tables():
    """Return enriched table metadata with row counts and sample data."""
    tables = get_tables_metadata()
    return {"tables": tables}


# ── Generate ───────────────────────────────────────────────


@router.post("/generate", response_model=GenerateResponse)
async def generate_sql(payload: GenerateRequest):
    """Convert a natural language prompt into an SQL query."""
    logger.info("Generate request: %s", payload.prompt[:80])
    sql, mode = create_sql_from_nl(payload.prompt)
    return GenerateResponse(sql=sql, ai_mode=mode)


# ── Execute ────────────────────────────────────────────────


@router.post("/execute")
async def execute(payload: ExecuteRequest):
    """Execute a SQL query against the database and return results."""
    logger.info("Execute request: %s", payload.sql[:80])
    result = execute_query(payload.sql)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return JSONResponse(content={
        "columns": result["columns"],
        "rows": result["rows"],
        "row_count": result["row_count"],
    })
