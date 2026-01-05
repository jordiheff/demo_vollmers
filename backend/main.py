"""
FastAPI application entry point for Nutrition Label Generator.

Modified for demo deployment - serves frontend static files.
"""

import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from database.connection import init_db
from routers import extract_router, calculate_router, label_router, usda_router, recipe_router
from logging_config import setup_logging, get_logger
from errors import AppException, app_exception_handler, generic_exception_handler

# Determine base path (for PyInstaller compatibility)
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = sys._MEIPASS
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Initialize rate limiter
# Default: 100 requests per minute for general endpoints
# Toggle via RATE_LIMIT_ENABLED env var (default: False for development)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    enabled=settings.rate_limit_enabled  # Easy toggle for dev/prod
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Nutrition Label Generator", data={"version": "1.0.0"})
    init_db()
    logger.info("Database initialized")
    logger.info("Rate limiting status", data={
        "enabled": settings.rate_limit_enabled,
        "note": "Set RATE_LIMIT_ENABLED=true for production"
    })
    yield
    # Shutdown
    logger.info("Shutting down Nutrition Label Generator")


app = FastAPI(
    title="Nutrition Label Generator",
    description="Generate FDA-compliant nutrition labels from supplier spec sheets",
    version="1.0.0",
    lifespan=lifespan
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(extract_router)
app.include_router(calculate_router)
app.include_router(label_router)
app.include_router(usda_router)
app.include_router(recipe_router)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Health check endpoint (available even without frontend)
@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "openai_configured": bool(settings.openai_api_key),
        "usda_configured": bool(settings.usda_api_key),
    }


# Static file serving for demo deployment
# Check for static files in multiple locations for flexibility
static_paths = [
    os.path.join(BASE_DIR, "static"),           # PyInstaller bundled location
    os.path.join(BASE_DIR, "..", "static"),     # Development location (sibling to backend)
    os.path.join(os.path.dirname(BASE_DIR), "static"),  # Alternative dev location
]

STATIC_DIR = None
for path in static_paths:
    if os.path.exists(path) and os.path.isdir(path):
        STATIC_DIR = os.path.abspath(path)
        break

if STATIC_DIR:
    logger.info("Serving frontend static files", data={"path": STATIC_DIR})

    # Mount assets directory
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Serve index.html for root and any unmatched routes (SPA routing)
    @app.get("/")
    async def serve_frontend():
        """Serve the frontend application."""
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """
        Catch-all route for SPA routing.
        Serves static files if they exist, otherwise returns index.html.
        """
        # Check if it's a static file request
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # For all other routes, return index.html (SPA routing)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    logger.info("No static files found - running in API-only mode")

    @app.get("/")
    async def root():
        """Health check endpoint (API-only mode)."""
        return {
            "status": "ok",
            "app": "Nutrition Label Generator",
            "version": "1.0.0",
            "mode": "api-only",
            "note": "Frontend not bundled. Access API endpoints at /api/*"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
