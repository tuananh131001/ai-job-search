"""LinkedIn job scraper for Marketing Junior positions in Vietnam."""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode, quote

from bs4 import BeautifulSoup

from app.models import JobSource
from .base import BaseScraper, JobData, ScrapingError


class LinkedInScraper(BaseScraper):
    """
    LinkedIn job scraper optimized for Marketing Junior positions in Vietnam.
    
    Note: LinkedIn has strict anti-bot measures. This implementation focuses
    on public job listings and respects LinkedIn's terms of service.
    """
    
    def __init__(self, **kwargs):
        """Initialize LinkedIn scraper with conservative settings."""
        super().__init__(
            requests_per_minute=10,  # Very conservative for LinkedIn
            timeout=30,
            max_retries=2,
            retry_delay=3.0,
            **kwargs
        )
        
        self.base_url = "https://www.linkedin.com"
        self.jobs_search_url = f"{self.base_url}/jobs/search"
        
        # LinkedIn-specific headers to appear more browser-like
        self.linkedin_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        
    def get_job_source(self) -> JobSource:
        """Return LinkedIn as the job source."""
        return JobSource.LINKEDIN
        
    async def search_jobs(
        self,
        keywords: List[str],
        location: str = "Vietnam",
        max_pages: int = 3,  # Keep low for LinkedIn
    ) -> List[JobData]:
        """
        Search for Marketing Junior jobs on LinkedIn.
        
        Args:
            keywords: Marketing-related keywords to search for
            location: Location to search (default: Vietnam)
            max_pages: Maximum pages to scrape (kept low for LinkedIn)
            
        Returns:
            List[JobData]: List of scraped job data
        """
        self.logger.info(f"Starting LinkedIn search for keywords: {keywords}, location: {location}")
        
        all_jobs = []
        
        # Combine keywords for search query
        query = " ".join(keywords)
        
        for page in range(max_pages):
            try:
                start_index = page * 25  # LinkedIn typically shows 25 jobs per page
                jobs_page = await self._scrape_search_page(query, location, start_index)
                
                if not jobs_page:
                    self.logger.info(f"No more jobs found on page {page + 1}, stopping")
                    break
                    
                all_jobs.extend(jobs_page)
                self.logger.info(f"Scraped {len(jobs_page)} jobs from page {page + 1}")
                
                # Add longer delay between pages for LinkedIn
                if page < max_pages - 1:
                    await asyncio.sleep(5)
                    
            except ScrapingError as e:
                self.logger.error(f"Error scraping page {page + 1}: {e}")
                break
                
        # Filter for Marketing Junior positions
        filtered_jobs = [
            job for job in all_jobs 
            if self.is_marketing_junior_job(job.title, job.description)
        ]
        
        self.logger.info(f"Found {len(filtered_jobs)} Marketing Junior jobs out of {len(all_jobs)} total")
        return filtered_jobs
        
    async def _scrape_search_page(
        self,
        query: str,
        location: str,
        start: int = 0
    ) -> List[JobData]:
        """
        Scrape a single search results page from LinkedIn.
        
        Args:
            query: Search query
            location: Location filter
            start: Starting index for pagination
            
        Returns:
            List[JobData]: Jobs found on this page
        """
        # Build search URL with parameters
        params = {
            'keywords': query,
            'location': location,
            'start': start,
            'sortBy': 'DD',  # Sort by date (most recent)
            'f_TPR': 'r604800',  # Jobs posted in last week
            'f_E': '2',  # Entry level (1=internship, 2=entry, 3=associate, 4=mid-senior, 5=director, 6=executive)
        }
        
        search_url = f"{self.jobs_search_url}?{urlencode(params)}"
        self.logger.debug(f"Scraping LinkedIn search page: {search_url}")
        
        # Make request with LinkedIn-specific headers
        async with await self.make_request(search_url, headers=self.linkedin_headers) as response:
            html = await response.text()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # LinkedIn uses various job card selectors
        job_cards = soup.find_all(['div', 'li'], class_=re.compile(r'job-search-card|jobs-search__results-list|base-search-card'))
        
        if not job_cards:
            # Try alternative selector patterns
            job_cards = soup.find_all('div', {'data-entity-urn': re.compile(r'job')})
            
        if not job_cards:
            self.logger.warning("No job cards found on LinkedIn page")
            return []
            
        jobs = []
        for card in job_cards:
            try:
                job_data = await self._extract_job_from_card(card)
                if job_data:
                    jobs.append(job_data)
            except Exception as e:
                self.logger.warning(f"Error extracting job from LinkedIn card: {e}")
                continue
                
        return jobs
        
    async def _extract_job_from_card(self, card) -> Optional[JobData]:
        """
        Extract job information from a LinkedIn job card element.
        
        Args:
            card: BeautifulSoup element representing a job card
            
        Returns:
            Optional[JobData]: Extracted job data or None if extraction fails
        """
        try:
            # Extract job title and URL
            title_element = (
                card.find('a', class_=re.compile(r'job-search-card__title-link')) or
                card.find('h3', class_=re.compile(r'base-search-card__title')) or
                card.find('a', href=re.compile(r'/jobs/view/'))
            )
            
            if not title_element:
                return None
                
            # Get title text
            title = self.clean_text(title_element.get_text(strip=True))
            
            # Get job URL
            job_url = title_element.get('href', '')
            if job_url:
                job_url = self.normalize_url(job_url, self.base_url)
                
            # Extract job ID from URL or data attributes
            external_id = None
            if job_url:
                # LinkedIn job URLs: /jobs/view/<id>/
                match = re.search(r'/jobs/view/(\d+)', job_url)
                if match:
                    external_id = match.group(1)
                    
            # Try data attributes
            if not external_id:
                urn = card.get('data-entity-urn', '')
                if urn:
                    match = re.search(r':(\d+)$', urn)
                    if match:
                        external_id = match.group(1)
                        
            if not external_id:
                return None
                
            # Extract company name
            company_element = (
                card.find('a', class_=re.compile(r'job-search-card__subtitle-link')) or
                card.find('h4', class_=re.compile(r'base-search-card__subtitle')) or
                card.find('span', class_=re.compile(r'job-search-card__company-name'))
            )
            
            company_name = "Unknown Company"
            if company_element:
                company_name = self.clean_text(company_element.get_text(strip=True))
                
            # Extract location
            location_element = (
                card.find('span', class_=re.compile(r'job-search-card__location')) or
                card.find('div', class_=re.compile(r'base-search-card__metadata'))
            )
            
            location = "Vietnam"
            if location_element:
                location_text = location_element.get_text(strip=True)
                # Extract just the location part if there's additional metadata
                location = self.clean_text(location_text.split('•')[0])
                
            # Extract job description/snippet
            description_element = (
                card.find('p', class_=re.compile(r'job-search-card__snippet')) or
                card.find('div', class_=re.compile(r'base-search-card__metadata'))
            )
            
            description = ""
            if description_element:
                description = self.clean_text(description_element.get_text(strip=True))
                
            # Try to get more detailed description by visiting job page
            if job_url:
                full_description = await self._get_job_description(job_url)
                if full_description:
                    description = full_description
                    
            # Extract posted date
            date_element = card.find('time', class_=re.compile(r'job-search-card__listdate'))
            posted_date = None
            if date_element:
                # Try datetime attribute first
                datetime_attr = date_element.get('datetime')
                if datetime_attr:
                    try:
                        posted_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    except ValueError:
                        pass
                        
                # Fallback to parsing text
                if not posted_date:
                    date_text = date_element.get_text(strip=True)
                    posted_date = self._parse_date(date_text)
                    
            # Determine experience level
            experience_level = self.extract_experience_level(title, description)
            
            return JobData(
                external_id=f"linkedin_{external_id}",
                title=title,
                company_name=company_name,
                description=description,
                location=location,
                url=job_url,
                source=JobSource.LINKEDIN,
                job_type="full-time",  # Default
                experience_level=experience_level,
                salary_min=None,  # LinkedIn rarely shows salary on cards
                salary_max=None,
                salary_currency="VND",
                posted_date=posted_date,
                is_active=True,
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting LinkedIn job data: {e}")
            return None
            
    async def _get_job_description(self, job_url: str) -> Optional[str]:
        """
        Get detailed job description from LinkedIn job detail page.
        
        Note: This method is conservative due to LinkedIn's anti-bot measures.
        
        Args:
            job_url: URL of the job detail page
            
        Returns:
            Optional[str]: Full job description or None if failed
        """
        try:
            # Add extra delay for job detail page requests
            await asyncio.sleep(2)
            
            async with await self.make_request(job_url, headers=self.linkedin_headers) as response:
                html = await response.text()
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for job description container
            description_container = (
                soup.find('div', class_=re.compile(r'show-more-less-html__markup')) or
                soup.find('div', class_=re.compile(r'jobs-description-content__text')) or
                soup.find('section', class_=re.compile(r'jobs-description'))
            )
            
            if description_container:
                # Extract text while preserving some structure
                description = self.clean_text(description_container.get_text(separator=' ', strip=True))
                return description[:2000]  # Limit description length
                
        except Exception as e:
            self.logger.warning(f"Failed to get LinkedIn job description from {job_url}: {e}")
            
        return None
        
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse posted date from LinkedIn date text.
        
        Args:
            date_text: Date text from LinkedIn (e.g., "2 days ago", "1 week ago")
            
        Returns:
            Optional[datetime]: Parsed date or None
        """
        if not date_text:
            return None
            
        date_text = date_text.lower().strip()
        now = datetime.utcnow()
        
        # Parse relative dates
        if any(word in date_text for word in ['today', 'just now', 'few minutes']):
            return now
        elif 'yesterday' in date_text:
            return now - timedelta(days=1)
        elif 'day' in date_text:
            days_match = re.search(r'(\d+)\s*day', date_text)
            if days_match:
                days = int(days_match.group(1))
                return now - timedelta(days=days)
        elif 'week' in date_text:
            weeks_match = re.search(r'(\d+)\s*week', date_text)
            if weeks_match:
                weeks = int(weeks_match.group(1))
                return now - timedelta(weeks=weeks)
        elif 'month' in date_text:
            months_match = re.search(r'(\d+)\s*month', date_text)
            if months_match:
                months = int(months_match.group(1))
                return now - timedelta(days=months * 30)
                
        return None
        
    def is_marketing_junior_job(self, title: str, description: str) -> bool:
        """
        Enhanced marketing junior job detection for LinkedIn.
        
        LinkedIn typically has more detailed job titles and descriptions,
        so we can be more specific in our filtering.
        """
        # Call parent method first
        if not super().is_marketing_junior_job(title, description):
            return False
            
        # Additional LinkedIn-specific filtering
        title_lower = title.lower()
        description_lower = description.lower()
        
        # Exclude clearly senior positions
        exclude_keywords = [
            'senior', 'sr.', 'lead', 'manager', 'director', 'head of',
            'vp', 'vice president', 'principal', 'architect', 'chief'
        ]
        
        if any(keyword in title_lower for keyword in exclude_keywords):
            return False
            
        # Prefer positions that explicitly mention marketing disciplines
        preferred_marketing = [
            'digital marketing', 'content marketing', 'social media marketing',
            'performance marketing', 'growth marketing', 'marketing automation',
            'email marketing', 'affiliate marketing', 'influencer marketing'
        ]
        
        has_preferred = any(keyword in title_lower or keyword in description_lower 
                           for keyword in preferred_marketing)
        
        return has_preferred