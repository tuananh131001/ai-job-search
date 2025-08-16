"""Scraping manager for coordinating multiple job scrapers."""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Type
from dataclasses import asdict

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import Job, Company, JobSource
from app.database.session import get_db
from .base import BaseScraper, JobData, ScrapingError
from .indeed import IndeedScraper
from .linkedin import LinkedInScraper


class ScrapingManager:
    """
    Manages multiple job scrapers with centralized configuration and database integration.
    
    Handles scraper orchestration, data deduplication, database storage,
    and provides comprehensive logging and error handling.
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize scraping manager.
        
        Args:
            db_session: Database session (optional, will create if not provided)
        """
        self.db_session = db_session
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Available scrapers
        self.scrapers: Dict[str, Type[BaseScraper]] = {
            'indeed': IndeedScraper,
            'linkedin': LinkedInScraper,
        }
        
        # Default marketing keywords for Vietnam market
        self.default_keywords = [
            'marketing junior',
            'digital marketing',
            'content marketing',
            'social media marketing',
            'marketing executive',
            'marketing specialist',
            'marketing coordinator',
            'marketing assistant',
        ]
        
    async def scrape_all_sources(
        self,
        keywords: Optional[List[str]] = None,
        location: str = "Vietnam",
        max_pages_per_source: int = 3,
        sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Scrape jobs from all configured sources concurrently.
        
        Args:
            keywords: Marketing keywords to search for
            location: Location filter
            max_pages_per_source: Maximum pages per scraper
            sources: Specific sources to scrape (default: all)
            
        Returns:
            Dict with scraping results and statistics
        """
        if keywords is None:
            keywords = self.default_keywords
            
        if sources is None:
            sources = list(self.scrapers.keys())
            
        self.logger.info(f"Starting scraping for sources: {sources}")
        
        # Create scraping tasks
        tasks = []
        for source in sources:
            if source in self.scrapers:
                task = self._scrape_source(
                    source=source,
                    keywords=keywords,
                    location=location,
                    max_pages=max_pages_per_source
                )
                tasks.append(task)
            else:
                self.logger.warning(f"Unknown scraper source: {source}")
                
        # Run all scrapers concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        all_jobs = []
        source_stats = {}
        errors = []
        
        for i, result in enumerate(results):
            source = sources[i] if i < len(sources) else f"unknown_{i}"
            
            if isinstance(result, Exception):
                self.logger.error(f"Scraping failed for {source}: {result}")
                errors.append(f"{source}: {str(result)}")
                source_stats[source] = {'jobs_found': 0, 'error': str(result)}
            else:
                jobs, stats = result
                all_jobs.extend(jobs)
                source_stats[source] = stats
                self.logger.info(f"{source}: Found {len(jobs)} jobs")
                
        # Deduplicate jobs
        unique_jobs = self._deduplicate_jobs(all_jobs)
        self.logger.info(f"After deduplication: {len(unique_jobs)} unique jobs")
        
        # Save to database if session provided
        saved_count = 0
        if self.db_session:
            saved_count = await self._save_jobs_to_db(unique_jobs)
            
        return {
            'total_jobs_found': len(all_jobs),
            'unique_jobs': len(unique_jobs),
            'jobs_saved': saved_count,
            'source_statistics': source_stats,
            'errors': errors,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
    async def _scrape_source(
        self,
        source: str,
        keywords: List[str],
        location: str,
        max_pages: int,
    ) -> tuple[List[JobData], Dict[str, Any]]:
        """
        Scrape jobs from a single source.
        
        Args:
            source: Source name (e.g., 'indeed', 'linkedin')
            keywords: Search keywords
            location: Location filter
            max_pages: Maximum pages to scrape
            
        Returns:
            Tuple of (jobs_list, statistics_dict)
        """
        scraper_class = self.scrapers[source]
        stats = {
            'jobs_found': 0,
            'pages_scraped': 0,
            'marketing_junior_jobs': 0,
            'start_time': datetime.utcnow().isoformat(),
        }
        
        try:
            async with scraper_class() as scraper:
                self.logger.info(f"Starting {source} scraper")
                
                jobs = await scraper.search_jobs(
                    keywords=keywords,
                    location=location,
                    max_pages=max_pages,
                )
                
                # Count marketing junior specific jobs
                marketing_junior_count = sum(
                    1 for job in jobs 
                    if scraper.is_marketing_junior_job(job.title, job.description)
                )
                
                stats.update({
                    'jobs_found': len(jobs),
                    'marketing_junior_jobs': marketing_junior_count,
                    'end_time': datetime.utcnow().isoformat(),
                    'success': True,
                })
                
                return jobs, stats
                
        except Exception as e:
            stats.update({
                'end_time': datetime.utcnow().isoformat(),
                'success': False,
                'error': str(e),
            })
            raise ScrapingError(f"Failed to scrape {source}: {e}")
            
    def _deduplicate_jobs(self, jobs: List[JobData]) -> List[JobData]:
        """
        Remove duplicate jobs based on URL and external_id.
        
        Args:
            jobs: List of job data
            
        Returns:
            List of unique jobs
        """
        seen_urls = set()
        seen_external_ids = set()
        unique_jobs = []
        
        for job in jobs:
            # Use URL as primary deduplication key
            if job.url and job.url not in seen_urls:
                seen_urls.add(job.url)
                unique_jobs.append(job)
            # Fallback to external_id if no URL
            elif job.external_id and job.external_id not in seen_external_ids:
                seen_external_ids.add(job.external_id)
                unique_jobs.append(job)
                
        return unique_jobs
        
    async def _save_jobs_to_db(self, jobs: List[JobData]) -> int:
        """
        Save jobs to database with company resolution.
        
        Args:
            jobs: List of job data to save
            
        Returns:
            Number of jobs successfully saved
        """
        if not self.db_session:
            return 0
            
        saved_count = 0
        
        for job_data in jobs:
            try:
                # Find or create company
                company = self._find_or_create_company(
                    name=job_data.company_name,
                    industry="Marketing & Advertising"  # Default for our use case
                )
                
                # Check if job already exists (by external_id or URL)
                existing_job = (
                    self.db_session.query(Job)
                    .filter(
                        (Job.external_id == job_data.external_id) |
                        (Job.url == job_data.url)
                    )
                    .first()
                )
                
                if existing_job:
                    # Update existing job
                    self._update_job_from_data(existing_job, job_data, company.id)
                    self.logger.debug(f"Updated existing job: {job_data.title}")
                else:
                    # Create new job
                    new_job = self._create_job_from_data(job_data, company.id)
                    self.db_session.add(new_job)
                    self.logger.debug(f"Created new job: {job_data.title}")
                    
                saved_count += 1
                
            except IntegrityError as e:
                self.logger.warning(f"Integrity error saving job {job_data.title}: {e}")
                self.db_session.rollback()
                continue
            except Exception as e:
                self.logger.error(f"Error saving job {job_data.title}: {e}")
                self.db_session.rollback()
                continue
                
        try:
            self.db_session.commit()
            self.logger.info(f"Successfully saved {saved_count} jobs to database")
        except Exception as e:
            self.logger.error(f"Error committing jobs to database: {e}")
            self.db_session.rollback()
            saved_count = 0
            
        return saved_count
        
    def _find_or_create_company(self, name: str, industry: str = None) -> Company:
        """
        Find existing company or create new one.
        
        Args:
            name: Company name
            industry: Company industry
            
        Returns:
            Company instance
        """
        # Try to find existing company by name
        company = (
            self.db_session.query(Company)
            .filter(Company.name.ilike(f"%{name}%"))
            .first()
        )
        
        if not company:
            company = Company(
                name=name,
                industry=industry,
            )
            self.db_session.add(company)
            self.db_session.flush()  # Get the ID
            
        return company
        
    def _create_job_from_data(self, job_data: JobData, company_id: int) -> Job:
        """
        Create Job instance from JobData.
        
        Args:
            job_data: JobData instance
            company_id: Company ID
            
        Returns:
            Job instance
        """
        return Job(
            external_id=job_data.external_id,
            title=job_data.title,
            company_id=company_id,
            description=job_data.description,
            location=job_data.location,
            url=job_data.url,
            source=job_data.source,
            job_type=job_data.job_type,
            experience_level=job_data.experience_level,
            salary_min=job_data.salary_min,
            salary_max=job_data.salary_max,
            salary_currency=job_data.salary_currency,
            posted_date=job_data.posted_date,
            is_active=job_data.is_active,
        )
        
    def _update_job_from_data(self, job: Job, job_data: JobData, company_id: int) -> None:
        """
        Update existing Job with new data.
        
        Args:
            job: Existing Job instance
            job_data: New JobData
            company_id: Company ID
        """
        job.title = job_data.title
        job.company_id = company_id
        job.description = job_data.description
        job.location = job_data.location
        job.job_type = job_data.job_type
        job.experience_level = job_data.experience_level
        job.salary_min = job_data.salary_min
        job.salary_max = job_data.salary_max
        job.salary_currency = job_data.salary_currency
        job.posted_date = job_data.posted_date
        job.is_active = job_data.is_active
        
    async def get_scraping_status(self) -> Dict[str, Any]:
        """
        Get current status of available scrapers.
        
        Returns:
            Dictionary with scraper status information
        """
        status = {
            'available_scrapers': list(self.scrapers.keys()),
            'default_keywords': self.default_keywords,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Test connectivity for each scraper (simple health check)
        scraper_health = {}
        for source, scraper_class in self.scrapers.items():
            try:
                async with scraper_class() as scraper:
                    # Simple connectivity test
                    scraper_health[source] = {
                        'status': 'healthy',
                        'requests_per_minute': scraper.requests_per_minute,
                    }
            except Exception as e:
                scraper_health[source] = {
                    'status': 'unhealthy',
                    'error': str(e),
                }
                
        status['scraper_health'] = scraper_health
        return status