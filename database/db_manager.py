"""
Database manager for the AI SQL Query Generator.

Creates and configures a SQLAlchemy engine connected to a SQLite
database. The database file is stored in ``database/generated.db``
by default and can be changed via the ``DATABASE_URL`` setting.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Engine setup ──────────────────────────────────────────

DATABASE_URL = settings.DATABASE_URL

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    logger.info("SQLite engine created: %s", DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL)
    logger.info("Database engine created: %s", DATABASE_URL.split("@")[-1])

# ── Session & Base ────────────────────────────────────────

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session.

    Usage::

        @router.get("/example")
        def example(db=Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
