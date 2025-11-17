"""
Main FastAPI application entry point for BOMA.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.api.v1 import api_router
from app.api.middleware.request_logger import RequestLoggerMiddleware
from app.api.middleware.error_handler import ErrorHandlerMiddleware
from app.db.session import init_db, close_db

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(
        "Starting BOMA application",
        extra={
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
    )

    # Initialize database connection pool
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database: %s", str(e), exc_info=True)
        raise

    # TODO: Initialize Redis connection
    # TODO: Verify external service connections

    yield

    # Shutdown
    logger.info("Shutting down BOMA application")

    # Close database connections
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database: %s", str(e), exc_info=True)

    # TODO: Close Redis connections
    # TODO: Cleanup resources


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Tanzania-focused short-stay and mid-stay rental marketplace",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Trusted Host Middleware (for production)
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[
                "boma.rekonify.org",
                "*.boma.co.tz",
                "boma.co.tz"
            ]
        )

    # Custom Middlewares
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggerMiddleware)

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return JSONResponse(
            content={
                "status": "healthy",
                "app": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
            }
        )

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to BOMA API",
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.is_development else None,
        }

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Mount static files for serving uploads
    uploads_dir = Path(settings.UPLOAD_DIR)
    if not uploads_dir.exists():
        uploads_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created uploads directory: {uploads_dir.absolute()}")

    app.mount(
        settings.STATIC_URL,
        StaticFiles(directory=str(uploads_dir)),
        name="static"
    )
    logger.info(f"Mounted static files: {settings.STATIC_URL} -> {uploads_dir.absolute()}")

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        log_config=None,  # We handle logging ourselves
    )
