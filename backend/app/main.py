from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import api_router
from app.database.session import engine, Base

# Create tables if they don't exist (only if not in test mode)
import os
if not os.getenv("TESTING"):
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="Job Scraper API focused on Marketing Junior positions in Vietnam"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include main API router
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Job Scraper API - Marketing Junior Focus",
        "version": settings.app_version,
        "docs": "/docs",
        "endpoints": {
            "health": "/api/health",
            "database_stats": "/api/database/stats",
            "scrape_jobs": "/api/scrapers/scrape",
            "scraper_status": "/api/scrapers/status",
            "available_sources": "/api/scrapers/sources"
        }
    }