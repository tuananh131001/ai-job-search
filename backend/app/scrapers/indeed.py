"""Indeed job scraper for Marketing Junior positions in Vietnam."""

import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode, urlparse

from bs4 import BeautifulSoup

from app.models import JobSource
from .base import BaseScraper, JobData, ScrapingError


class IndeedScraper(BaseScraper):
    """
    Indeed job scraper optimized for Marketing Junior positions in Vietnam.
    
    Implements ethical scraping with rate limiting and handles Indeed's
    anti-bot measures while focusing on Marketing Junior job listings.
    """
    
    def __init__(self, **kwargs):
        """Initialize Indeed scraper with Vietnam-specific settings."""
        super().__init__(
            requests_per_minute=20,  # Conservative rate limiting for Indeed
            timeout=30,
            max_retries=3,
            retry_delay=2.0,
            **kwargs
        )
        
        self.base_url = "https://vn.indeed.com"
        self.search_url = f"{self.base_url}/jobs"
        
        # Indeed-specific headers
        self.indeed_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }
        
    def get_job_source(self) -> JobSource:
        """Return Indeed as the job source."""
        return JobSource.INDEED
        
    async def search_jobs(
        self,
        keywords: List[str],
        location: str = "Vietnam",
        max_pages: int = 5,
    ) -> List[JobData]:
        """
        Search for Marketing Junior jobs on Indeed Vietnam.
        
        Args:
            keywords: Marketing-related keywords to search for
            location: Location to search (default: Vietnam)
            max_pages: Maximum pages to scrape
            
        Returns:
            List[JobData]: List of scraped job data
        """
        self.logger.info(f"Starting Indeed search for keywords: {keywords}, location: {location}")
        
        all_jobs = []
        
        # Combine keywords for search query
        query = " ".join(keywords)
        
        for page in range(max_pages):
            try:
                jobs_page = await self._scrape_search_page(query, location, page * 10)
                if not jobs_page:
                    self.logger.info(f"No more jobs found on page {page + 1}, stopping")
                    break
                    
                all_jobs.extend(jobs_page)
                self.logger.info(f"Scraped {len(jobs_page)} jobs from page {page + 1}")
                
                # Add delay between pages to be respectful
                if page < max_pages - 1:
                    await asyncio.sleep(2)
                    
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
        Scrape a single search results page from Indeed.
        
        Args:
            query: Search query
            location: Location filter
            start: Starting index for pagination
            
        Returns:
            List[JobData]: Jobs found on this page
        """
        # Build search URL with parameters
        params = {
            'q': query,
            'l': location,
            'start': start,
            'sort': 'date',  # Sort by most recent
            'filter': 0,  # Include all job types
        }
        
        search_url = f"{self.search_url}?{urlencode(params)}"
        self.logger.debug(f"Scraping search page: {search_url}")
        
        # Make request with Indeed-specific headers
        async with await self.make_request(search_url, headers=self.indeed_headers) as response:
            html = await response.text()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find job cards - Indeed uses various selectors
        job_cards = soup.find_all(['div'], class_=re.compile(r'job_seen_beacon|result|jobsearch-SerpJobCard'))
        
        if not job_cards:
            self.logger.warning("No job cards found on page")
            return []
            
        jobs = []
        for card in job_cards:
            try:
                job_data = await self._extract_job_from_card(card)
                if job_data:
                    jobs.append(job_data)
            except Exception as e:
                self.logger.warning(f"Error extracting job from card: {e}")
                continue
                
        return jobs
        
    async def _extract_job_from_card(self, card) -> Optional[JobData]:
        """
        Extract job information from a job card element.
        
        Args:
            card: BeautifulSoup element representing a job card
            
        Returns:
            Optional[JobData]: Extracted job data or None if extraction fails
        """
        try:
            # Extract job title and URL
            title_element = card.find('a', {'data-jk': True}) or card.find('h2', class_=re.compile(r'jobTitle'))
            if not title_element:
                return None
                
            # Get title text
            title_link = title_element.find('span') or title_element
            title = self.clean_text(title_link.get_text(strip=True))
            
            # Get job URL
            job_url = title_element.get('href', '')
            if job_url:
                job_url = self.normalize_url(job_url, self.base_url)
                
            # Extract job ID from data-jk attribute or URL
            external_id = title_element.get('data-jk')
            if not external_id and job_url:
                # Try to extract from URL pattern: /jobs?jk=<id>
                match = re.search(r'jk=([a-f0-9]+)', job_url)
                if match:
                    external_id = match.group(1)
                    
            if not external_id:
                return None
                
            # Extract company name
            company_element = card.find('span', class_=re.compile(r'companyName'))
            company_name = "Unknown Company"
            if company_element:
                company_link = company_element.find('a') or company_element
                company_name = self.clean_text(company_link.get_text(strip=True))
                
            # Extract location
            location_element = card.find('div', class_=re.compile(r'companyLocation'))
            location = "Vietnam"
            if location_element:
                location = self.clean_text(location_element.get_text(strip=True))
                
            # Extract salary if available
            salary_element = card.find('span', class_=re.compile(r'salary|salaryText'))
            salary_min, salary_max = None, None
            if salary_element:
                salary_text = salary_element.get_text(strip=True)
                salary_min, salary_max = self._parse_salary(salary_text)
                
            # Extract job description snippet
            description_element = card.find('div', class_=re.compile(r'summary|snippet'))
            description = ""
            if description_element:
                description = self.clean_text(description_element.get_text(strip=True))
                
            # Try to get more detailed description by visiting job page
            if job_url:
                full_description = await self._get_job_description(job_url)
                if full_description:
                    description = full_description
                    
            # Extract posted date
            date_element = card.find('span', class_=re.compile(r'date'))
            posted_date = None
            if date_element:
                posted_date = self._parse_date(date_element.get_text(strip=True))
                
            # Determine experience level
            experience_level = self.extract_experience_level(title, description)
            
            return JobData(
                external_id=f"indeed_{external_id}",
                title=title,
                company_name=company_name,
                description=description,
                location=location,
                url=job_url,
                source=JobSource.INDEED,
                job_type="full-time",  # Default, could be extracted
                experience_level=experience_level,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency="VND",
                posted_date=posted_date,
                is_active=True,
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting job data: {e}")
            return None
            
    async def _get_job_description(self, job_url: str) -> Optional[str]:
        """
        Get detailed job description from job detail page.
        
        Args:
            job_url: URL of the job detail page
            
        Returns:
            Optional[str]: Full job description or None if failed
        """
        try:
            async with await self.make_request(job_url, headers=self.indeed_headers) as response:
                html = await response.text()
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for job description container
            description_container = (
                soup.find('div', {'id': 'jobDescriptionText'}) or
                soup.find('div', class_=re.compile(r'jobsearch-jobDescriptionText')) or
                soup.find('div', class_=re.compile(r'jobDescription'))
            )
            
            if description_container:
                # Extract text while preserving some structure
                description = self.clean_text(description_container.get_text(separator=' ', strip=True))
                return description[:2000]  # Limit description length
                
        except Exception as e:
            self.logger.warning(f"Failed to get job description from {job_url}: {e}")
            
        return None
        
    def _parse_salary(self, salary_text: str) -> tuple[Optional[float], Optional[float]]:
        """
        Parse salary information from text.
        
        Args:
            salary_text: Raw salary text from Indeed
            
        Returns:
            tuple: (salary_min, salary_max) in VND
        """
        if not salary_text:
            return None, None
            
        # Remove currency symbols and normalize
        normalized = re.sub(r'[^\d\-\s]', '', salary_text.replace(',', ''))
        
        # Look for salary ranges (e.g., "10-15", "10 - 15")
        range_match = re.search(r'(\d+)\s*-\s*(\d+)', normalized)
        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            
            # Convert to VND if needed (assuming millions)
            if min_val < 100:  # Likely in millions VND
                min_val *= 1_000_000
                max_val *= 1_000_000
                
            return min_val, max_val
            
        # Look for single salary value
        single_match = re.search(r'(\d+)', normalized)
        if single_match:
            salary = float(single_match.group(1))
            if salary < 100:  # Likely in millions VND
                salary *= 1_000_000
            return salary, salary
            
        return None, None
        
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse posted date from Indeed date text.
        
        Args:
            date_text: Date text from Indeed (e.g., "2 days ago", "1 week ago")
            
        Returns:
            Optional[datetime]: Parsed date or None
        """
        if not date_text:
            return None
            
        date_text = date_text.lower().strip()
        now = datetime.utcnow()
        
        # Parse relative dates
        if 'today' in date_text or 'just posted' in date_text:
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