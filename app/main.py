from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Import rate limiting components with fallback
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    RateLimitExceeded = Exception

from app.api.routes import analysis, status, results
from app.core.config import get_settings
from app.core.database import create_tables
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler
from app.utils.logging import setup_logging

# Initialize structured logging
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting AI Code Review Agent application")
    settings = get_settings()
    
    # Initialize database tables
    await create_tables()
    logger.info("Database tables initialized")
    
    yield
    
    logger.info("Shutting down AI Code Review Agent application")


def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="AI-powered code review agent for GitHub pull requests",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # Add rate limiting (only if slowapi is available)
    if SLOWAPI_AVAILABLE:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
        logger.info("Rate limiting enabled")
    else:
        logger.warning("Rate limiting disabled - slowapi not available")

    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.DEBUG else ["localhost", "127.0.0.1"]
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers with assignment-specified endpoints
    app.include_router(
        analysis.router,
        prefix="",  # No prefix for root-level endpoints
        tags=["analysis"]
    )
    app.include_router(
        status.router,
        prefix="",  # No prefix for root-level endpoints  
        tags=["status"]
    )
    app.include_router(
        results.router,
        prefix="",  # No prefix for root-level endpoints
        tags=["results"]
    )
    
    @app.get("/")
    async def root():
        """Root endpoint for health check."""
        return {
            "message": "AI Code Review Agent is running",
            "version": settings.VERSION,
            "status": "healthy"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": settings.VERSION}
    
    logger.info(
        "FastAPI application created",
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG
    )
    
    return app


# Create the application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
