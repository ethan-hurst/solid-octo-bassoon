"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.config.settings import settings
from src.api.routers import odds, alerts, analysis, live_betting
from src.api.websocket import websocket_router
from src.api.dependencies import (
    redis_pubsub_manager,
    connection_manager,
    cache_manager
)
from src.utils.logger import setup_logging

# Setup logging
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Sports Betting Edge Finder")
    
    # Connect to Redis
    await cache_manager.connect()
    await redis_pubsub_manager.connect()
    
    # Initialize database
    from src.api.dependencies import engine
    from src.models.database import Base
    
    async with engine.begin() as conn:
        # Create tables if they don't exist
        # In production, use Alembic migrations instead
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Disconnect from services
    await redis_pubsub_manager.disconnect()
    await cache_manager.disconnect()
    
    # Close database connections
    await engine.dispose()
    
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Real-time sports betting edge detection and analysis platform",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(
    odds.router,
    prefix="/api/odds",
    tags=["odds"]
)

app.include_router(
    alerts.router,
    prefix="/api/alerts",
    tags=["alerts"]
)

app.include_router(
    analysis.router,
    prefix="/api/analysis",
    tags=["analysis"]
)

app.include_router(
    live_betting.router,
    prefix="/api/live",
    tags=["live_betting"]
)

app.include_router(
    websocket_router,
    prefix="/ws",
    tags=["websocket"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Sports Betting Edge Finder API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "services": {
            "api": "up",
            "redis": "unknown",
            "database": "unknown",
            "websocket_connections": 0
        }
    }
    
    # Check Redis
    try:
        if cache_manager._redis:
            await cache_manager._redis.ping()
            health_status["services"]["redis"] = "up"
    except Exception:
        health_status["services"]["redis"] = "down"
        health_status["status"] = "degraded"
    
    # Check database
    try:
        from src.api.dependencies import engine
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        health_status["services"]["database"] = "up"
    except Exception:
        health_status["services"]["database"] = "down"
        health_status["status"] = "degraded"
    
    # Get WebSocket connections
    health_status["services"]["websocket_connections"] = (
        connection_manager.get_connection_count()
    )
    
    return health_status


# Metrics endpoint (simplified)
@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint."""
    from src.api.dependencies import get_odds_aggregator
    
    odds_aggregator = get_odds_aggregator(cache_manager)
    
    return {
        "api_requests_remaining": odds_aggregator.requests_remaining,
        "api_requests_used": odds_aggregator.requests_used,
        "active_websocket_connections": connection_manager.get_connection_count(),
        "connected_users": list(connection_manager.get_user_connections())
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )