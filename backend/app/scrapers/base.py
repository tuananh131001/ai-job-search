"""Base scraper class with async functionality and error handling."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

import aiohttp
from fake_useragent import UserAgent
from asyncio_throttle import Throttler

from app.models import JobSource


class ScrapingError(Exception):
    """Base exception for scraping errors."""
    pass


class RateLimitError(ScrapingError):
    """Exception raised when rate limit is exceeded."""
    pass


@dataclass
class JobData:
    """Data structure for scraped job information."""
    external_id: str
    title: str
    company_name: str
    description: str
    location: str
    url: str
    source: JobSource
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "VND"
    posted_date: Optional[datetime] = None
    is_active: bool = True


class BaseScraper(ABC):
    """
    Abstract base class for job scrapers with async functionality.
    
    Implements common functionality for rate limiting, session management,
    and error handling following ethical scraping practices.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 30,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize base scraper with rate limiting and session configuration.
        
        Args:
            requests_per_minute: Maximum requests per minute (rate limiting)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.requests_per_minute = requests_per_minute
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Rate limiting
        self.throttler = Throttler(rate_limit=requests_per_minute, period=60)
        
        # User agent rotation
        self.ua = UserAgent()
        
        # Session will be created in async context
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
        
    async def start_session(self) -> None:
        """Initialize aiohttp session with proper headers."""
        if self.session is None:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
                connector=connector,
            )
            
    async def close_session(self) -> None:
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def make_request(
        self,
        url: str,
        method: str = 'GET',
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Make rate-limited HTTP request with retry logic.
        
        Args:
            url: URL to request
            method: HTTP method
            **kwargs: Additional arguments for aiohttp request
            
        Returns:
            aiohttp.ClientResponse: Response object
            
        Raises:
            ScrapingError: If request fails after all retries
            RateLimitError: If rate limit is exceeded
        """
        if not self.session:
            await self.start_session()
            
        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting
                async with self.throttler:
                    # Rotate user agent occasionally
                    if attempt > 0:
                        self.session.headers['User-Agent'] = self.ua.random
                        
                    self.logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                    
                    async with self.session.request(method, url, **kwargs) as response:
                        # Check for rate limiting responses
                        if response.status == 429:
                            retry_after = response.headers.get('Retry-After', self.retry_delay)
                            self.logger.warning(f"Rate limited, waiting {retry_after}s")
                            await asyncio.sleep(float(retry_after))
                            continue
                            
                        # Check for other client/server errors
                        if response.status >= 400:
                            error_msg = f"HTTP {response.status} for {url}"
                            if attempt < self.max_retries:
                                self.logger.warning(f"{error_msg}, retrying...")
                                await asyncio.sleep(self.retry_delay * (2 ** attempt))
                                continue
                            else:
                                raise ScrapingError(error_msg)
                                
                        return response
                        
            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    self.logger.warning(f"Timeout for {url}, retrying...")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise ScrapingError(f"Timeout after {self.max_retries} retries for {url}")
                    
            except aiohttp.ClientError as e:
                if attempt < self.max_retries:
                    self.logger.warning(f"Client error for {url}: {e}, retrying...")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise ScrapingError(f"Client error after {self.max_retries} retries: {e}")
                    
        raise ScrapingError(f"Failed to make request to {url} after {self.max_retries} retries")
        
    @abstractmethod
    async def search_jobs(
        self,
        keywords: List[str],
        location: str = "Vietnam",
        max_pages: int = 5,
    ) -> List[JobData]:
        """
        Search for jobs with given keywords and location.
        
        Args:
            keywords: List of keywords to search for
            location: Location to search in
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List[JobData]: List of scraped job data
        """
        pass
        
    @abstractmethod
    def get_job_source(self) -> JobSource:
        """Return the job source for this scraper."""
        pass
        
    def is_marketing_junior_job(self, title: str, description: str) -> bool:
        """
        Check if job is relevant for Marketing Junior positions.
        
        Args:
            title: Job title
            description: Job description
            
        Returns:
            bool: True if job is relevant for Marketing Junior
        """
        marketing_keywords = [
            'marketing', 'digital marketing', 'content marketing', 
            'social media', 'seo', 'sem', 'ppc', 'campaign',
            'brand', 'advertising', 'promotion', 'communication'
        ]
        
        junior_keywords = [
            'junior', 'entry', 'fresh', 'graduate', 'intern',
            'trainee', 'assistant', '0-1 year', '0-2 year'
        ]
        
        title_lower = title.lower()
        description_lower = description.lower()
        
        # Check for marketing keywords
        has_marketing = any(keyword in title_lower or keyword in description_lower 
                           for keyword in marketing_keywords)
        
        # Check for junior level indicators
        has_junior = any(keyword in title_lower or keyword in description_lower 
                        for keyword in junior_keywords)
        
        return has_marketing and has_junior
        
    def extract_experience_level(self, title: str, description: str) -> Optional[str]:
        """
        Extract experience level from job title and description.
        
        Args:
            title: Job title
            description: Job description
            
        Returns:
            Optional[str]: Experience level ('entry' or 'junior')
        """
        text = f"{title} {description}".lower()
        
        if any(keyword in text for keyword in ['fresh', 'graduate', 'intern', 'trainee']):
            return 'entry'
        elif any(keyword in text for keyword in ['junior', '0-1 year', '0-2 year']):
            return 'junior'
            
        return None
        
    def normalize_url(self, url: str, base_url: str) -> str:
        """
        Normalize relative URLs to absolute URLs.
        
        Args:
            url: URL to normalize
            base_url: Base URL for relative URLs
            
        Returns:
            str: Normalized absolute URL
        """
        if not url:
            return ""
            
        # Handle relative URLs
        if url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return urljoin(base_url, url)
        elif not url.startswith(('http://', 'https://')):
            return urljoin(base_url, url)
            
        return url
        
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
            
        # Remove extra whitespace and normalize
        return ' '.join(text.strip().split())