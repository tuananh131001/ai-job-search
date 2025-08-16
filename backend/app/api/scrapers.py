"""API endpoints for job scraping functionality."""

import asyncio
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.session import get_db
from app.scrapers import ScrapingManager


router = APIRouter(prefix="/api/scrapers", tags=["scrapers"])


class ScrapeJobsRequest(BaseModel):
    """Request model for job scraping."""
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Marketing keywords to search for. Uses defaults if not provided."
    )
    location: str = Field(default="Vietnam", description="Location to search in")
    max_pages_per_source: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum pages to scrape per source (1-10)"
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description="Specific sources to scrape. Uses all if not provided."
    )


class ScrapeJobsResponse(BaseModel):
    """Response model for job scraping results."""
    total_jobs_found: int
    unique_jobs: int
    jobs_saved: int
    source_statistics: dict
    errors: List[str]
    timestamp: str


class ScrapingStatusResponse(BaseModel):
    """Response model for scraping status."""
    available_scrapers: List[str]
    default_keywords: List[str]
    scraper_health: dict
    timestamp: str


@router.post("/scrape", response_model=ScrapeJobsResponse)
async def scrape_jobs(
    request: ScrapeJobsRequest,
    db: Session = Depends(get_db)
) -> ScrapeJobsResponse:
    """
    Scrape jobs from configured sources.
    
    This endpoint initiates job scraping for Marketing Junior positions
    from Indeed and LinkedIn Vietnam. The scraping process includes:
    
    - Rate-limited requests to respect website terms
    - Filtering for Marketing Junior relevant positions
    - Deduplication of job listings
    - Database storage with company resolution
    
    Args:
        request: Scraping configuration parameters
        db: Database session dependency
        
    Returns:
        ScrapeJobsResponse: Scraping results and statistics
        
    Raises:
        HTTPException: If scraping configuration is invalid or scraping fails
    """
    try:
        # Validate sources if provided
        if request.sources:
            valid_sources = ['indeed', 'linkedin']
            invalid_sources = [s for s in request.sources if s not in valid_sources]
            if invalid_sources:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid scraping sources: {invalid_sources}. "
                           f"Valid sources are: {valid_sources}"
                )
        
        # Initialize scraping manager
        manager = ScrapingManager(db_session=db)
        
        # Perform scraping
        results = await manager.scrape_all_sources(
            keywords=request.keywords,
            location=request.location,
            max_pages_per_source=request.max_pages_per_source,
            sources=request.sources,
        )
        
        return ScrapeJobsResponse(**results)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


@router.post("/scrape/background")
async def scrape_jobs_background(
    request: ScrapeJobsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> dict:
    """
    Start job scraping in the background.
    
    This endpoint starts the scraping process as a background task,
    allowing the client to continue without waiting for completion.
    Use the /status endpoint to monitor progress.
    
    Args:
        request: Scraping configuration parameters
        background_tasks: FastAPI background tasks
        db: Database session dependency
        
    Returns:
        dict: Task initiation confirmation
        
    Raises:
        HTTPException: If scraping configuration is invalid
    """
    try:
        # Validate sources if provided
        if request.sources:
            valid_sources = ['indeed', 'linkedin']
            invalid_sources = [s for s in request.sources if s not in valid_sources]
            if invalid_sources:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid scraping sources: {invalid_sources}. "
                           f"Valid sources are: {valid_sources}"
                )
        
        # Add scraping task to background
        background_tasks.add_task(
            _background_scraping_task,
            request=request,
            db=db
        )
        
        return {
            "message": "Scraping task started in background",
            "keywords": request.keywords,
            "location": request.location,
            "sources": request.sources or ["indeed", "linkedin"],
            "max_pages_per_source": request.max_pages_per_source,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start background scraping: {str(e)}"
        )


@router.get("/status", response_model=ScrapingStatusResponse)
async def get_scraping_status() -> ScrapingStatusResponse:
    """
    Get current status of scraping infrastructure.
    
    Returns information about available scrapers, their health status,
    and default configuration parameters.
    
    Returns:
        ScrapingStatusResponse: Current scraping status and configuration
        
    Raises:
        HTTPException: If status check fails
    """
    try:
        manager = ScrapingManager()
        status = await manager.get_scraping_status()
        
        return ScrapingStatusResponse(**status)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scraping status: {str(e)}"
        )


@router.get("/sources")
async def get_available_sources() -> dict:
    """
    Get list of available scraping sources.
    
    Returns:
        dict: Available sources with their descriptions
    """
    return {
        "sources": {
            "indeed": {
                "name": "Indeed Vietnam",
                "url": "https://vn.indeed.com",
                "description": "Vietnam's leading job portal with extensive Marketing Junior listings",
                "rate_limit": "20 requests/minute",
                "features": ["salary_info", "company_details", "job_descriptions"]
            },
            "linkedin": {
                "name": "LinkedIn Jobs",
                "url": "https://www.linkedin.com/jobs",
                "description": "Professional network with high-quality Marketing positions",
                "rate_limit": "10 requests/minute",
                "features": ["company_details", "professional_networking", "detailed_descriptions"]
            }
        },
        "total_sources": 2
    }


@router.get("/keywords")
async def get_default_keywords() -> dict:
    """
    Get default Marketing Junior keywords used for scraping.
    
    Returns:
        dict: Default keyword configuration
    """
    manager = ScrapingManager()
    
    return {
        "default_keywords": manager.default_keywords,
        "keyword_count": len(manager.default_keywords),
        "description": "Default keywords optimized for Marketing Junior positions in Vietnam",
        "categories": {
            "general_marketing": ["marketing junior", "marketing executive", "marketing specialist"],
            "digital_marketing": ["digital marketing", "social media marketing", "content marketing"],
            "entry_level": ["marketing assistant", "marketing coordinator"]
        }
    }


@router.post("/test/{source}")
async def test_scraper_source(
    source: str,
    keywords: Optional[List[str]] = None
) -> dict:
    """
    Test a specific scraper source with limited scraping.
    
    This endpoint performs a lightweight test of a specific scraper
    to verify connectivity and basic functionality.
    
    Args:
        source: Source to test ('indeed' or 'linkedin')
        keywords: Optional test keywords
        
    Returns:
        dict: Test results
        
    Raises:
        HTTPException: If source is invalid or test fails
    """
    valid_sources = ['indeed', 'linkedin']
    if source not in valid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source: {source}. Valid sources are: {valid_sources}"
        )
    
    try:
        if keywords is None:
            keywords = ["marketing junior"]
            
        manager = ScrapingManager()
        
        # Perform limited test scraping (1 page only)
        jobs, stats = await manager._scrape_source(
            source=source,
            keywords=keywords,
            location="Vietnam",
            max_pages=1
        )
        
        return {
            "source": source,
            "test_status": "success",
            "jobs_found": len(jobs),
            "sample_job_titles": [job.title for job in jobs[:3]],  # First 3 titles
            "statistics": stats,
            "keywords_used": keywords
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test failed for {source}: {str(e)}"
        )


async def _background_scraping_task(request: ScrapeJobsRequest, db: Session) -> None:
    """
    Background task for job scraping.
    
    This function runs the scraping process in the background,
    allowing the API to return immediately while scraping continues.
    
    Args:
        request: Scraping configuration
        db: Database session
    """
    try:
        manager = ScrapingManager(db_session=db)
        
        results = await manager.scrape_all_sources(
            keywords=request.keywords,
            location=request.location,
            max_pages_per_source=request.max_pages_per_source,
            sources=request.sources,
        )
        
        # Log results (in production, you might want to store these in database)
        print(f"Background scraping completed: {results['unique_jobs']} jobs saved")
        
    except Exception as e:
        # Log error (in production, you might want to store this in database)
        print(f"Background scraping failed: {str(e)}")
        raise