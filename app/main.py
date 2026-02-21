"""
Darwix AI — Sales Call Intelligence Microservice

FastAPI application factory with lifecycle management,
middleware configuration, and structured error handling.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.exceptions import DarwixBaseError
from app.core.logging import get_logger, setup_logging
from app.db.models import Base
from app.db.session import engine
from app.schemas.models import ErrorResponse, HealthResponse

# ── Initialise logging ──────────────────────────────────────────────────
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


# ── Application Lifecycle ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize FFmpeg path for Whisper/STT
    try:
        from static_ffmpeg import add_paths
        add_paths()
        logger.info("FFmpeg paths added to environment")
    except ImportError:
        logger.warning("static-ffmpeg not installed, relying on system FFmpeg")

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")

    # Ensure directories exist
    settings.upload_path
    settings.output_path
    logger.info("Storage directories verified")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


# ── Application Factory ─────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-grade microservice for processing sales-call audio snippets. "
        "Provides speech-to-text with speaker diarization, sentiment analysis, "
        "coachable moment detection, and text-to-speech replay."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ── Middleware ───────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception Handlers ──────────────────────────────────────────────────

@app.exception_handler(DarwixBaseError)
async def darwix_error_handler(request: Request, exc: DarwixBaseError):
    """Handle application-specific errors with structured response."""
    logger.error(f"Application error: {exc.message}", extra={"extra_data": {"path": str(request.url)}})
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=type(exc).__name__,
            detail=exc.message,
            status_code=exc.status_code,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            detail="An unexpected error occurred. Please try again.",
            status_code=500,
        ).model_dump(),
    )


# ── Health Check ─────────────────────────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health check",
)
async def health_check():
    """Returns application health status."""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
    )


# ── Register Routes ─────────────────────────────────────────────────────

app.include_router(router, tags=["audio"])

logger.info(f"{settings.APP_NAME} application configured")
