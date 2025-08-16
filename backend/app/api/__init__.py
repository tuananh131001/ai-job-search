"""API package initialization."""

from fastapi import APIRouter
from .health import router as health_router
from .database import router as database_router
from .scrapers import router as scrapers_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(health_router)
api_router.include_router(database_router)
api_router.include_router(scrapers_router)

__all__ = ["api_router"]