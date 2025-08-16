from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import health, database
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

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(database.router, tags=["database"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to Job Scraper API - Marketing Junior Focus",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/health",
        "database_stats": "/api/database/stats"
    }