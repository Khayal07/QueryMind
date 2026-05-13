"""
AI SQL Query Generator — Application Entry Point.

Initialises the FastAPI application, loads Excel data into SQLite
on startup, configures CORS, and serves the React frontend from
the ``ui/dist`` directory when available.
"""

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import router
from core.excel_loader import load_excel_data
from core.schema_builder import initialize_database_from_excel
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Lifecycle ─────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load Excel data and build the SQLite schema on startup."""
    logger.info("=" * 60)
    logger.info("AI SQL Query Generator — starting up")
    logger.info("=" * 60)

    try:
        excel_path = load_excel_data()
        initialize_database_from_excel(excel_path)
        logger.info("Database schema built successfully.")
    except FileNotFoundError as exc:
        logger.warning("Startup warning: %s", exc)
    except Exception as exc:
        logger.error("Failed to initialise database: %s", exc, exc_info=True)

    ai_mode = "OpenAI" if settings.has_openai_key else "Fallback (no API key)"
    logger.info("AI mode: %s", ai_mode)
    logger.info("API available at http://%s:%s/api", settings.HOST, settings.PORT)
    logger.info("=" * 60)

    yield

    logger.info("Shutting down.")


# ── Application ───────────────────────────────────────────


app = FastAPI(
    title="AI SQL Query Generator",
    description="Convert natural language questions into SQL queries using AI.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server and common local origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the API router under /api
app.include_router(router, prefix="/api")

# Serve the production React build if it exists
ui_dist = Path(__file__).resolve().parent / "ui" / "dist"
if ui_dist.exists():
    app.mount("/", StaticFiles(directory=str(ui_dist), html=True), name="ui")


# ── Development runner ────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
