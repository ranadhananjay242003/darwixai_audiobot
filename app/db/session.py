"""
Database engine and session management.

Supports SQLite (development) and PostgreSQL (production) via DATABASE_URL.
Provides async-ready session factory with connection pooling.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _build_engine():
    """Create SQLAlchemy engine based on configuration."""
    settings = get_settings()
    url = settings.DATABASE_URL

    connect_args: dict = {}
    pool_kwargs: dict = {}

    if settings.is_sqlite:
        # SQLite-specific: enable WAL mode, foreign keys
        connect_args["check_same_thread"] = False
    else:
        # PostgreSQL / production DB: enable pooling
        pool_kwargs.update(
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,  # verify connections before use
        )

    engine = create_engine(
        url,
        echo=settings.DB_ECHO,
        connect_args=connect_args,
        **pool_kwargs,
    )

    # Enable WAL and foreign keys for SQLite
    if settings.is_sqlite:
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    logger.info("Database engine created", extra={"extra_data": {"url": url.split("@")[-1]}})
    return engine


engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.

    Usage:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
