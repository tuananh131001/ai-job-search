"""Job scraping package for Marketing Junior positions."""

from .base import BaseScraper, ScrapingError, RateLimitError
from .indeed import IndeedScraper
from .linkedin import LinkedInScraper
from .manager import ScrapingManager

__all__ = [
    "BaseScraper",
    "ScrapingError", 
    "RateLimitError",
    "IndeedScraper",
    "LinkedInScraper",
    "ScrapingManager",
]