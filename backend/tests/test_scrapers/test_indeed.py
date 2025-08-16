"""Tests for Indeed scraper functionality."""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from app.scrapers.indeed import IndeedScraper
from app.scrapers.base import JobData, ScrapingError
from app.models import JobSource


class TestIndeedScraper:
    """Test suite for IndeedScraper."""
    
    @pytest.fixture
    def scraper(self):
        """Create IndeedScraper instance for testing."""
        return IndeedScraper()
        
    def test_initialization(self, scraper):
        """Test IndeedScraper initialization."""
        assert scraper.requests_per_minute == 20  # Conservative for Indeed
        assert scraper.timeout == 30
        assert scraper.max_retries == 3
        assert scraper.retry_delay == 2.0
        assert scraper.base_url == "https://vn.indeed.com"
        assert scraper.search_url == "https://vn.indeed.com/jobs"
        
    def test_get_job_source(self, scraper):
        """Test job source identification."""
        assert scraper.get_job_source() == JobSource.INDEED
        
    @pytest.mark.asyncio
    @patch('app.scrapers.indeed.IndeedScraper._scrape_search_page')
    async def test_search_jobs(self, mock_scrape_page, scraper):
        """Test job search functionality."""
        # Mock search page results
        mock_jobs = [
            JobData(
                external_id="indeed_123",
                title="Marketing Junior Executive",
                company_name="Test Company",
                description="Marketing role for junior professionals...",
                location="Ho Chi Minh City",
                url="https://vn.indeed.com/job/123",
                source=JobSource.INDEED,
            ),
            JobData(
                external_id="indeed_456",
                title="Senior Software Engineer",  # Should be filtered out
                company_name="Tech Company",
                description="Senior engineering role...",
                location="Hanoi",
                url="https://vn.indeed.com/job/456",
                source=JobSource.INDEED,
            ),
        ]
        
        mock_scrape_page.side_effect = [mock_jobs, []]  # First page has jobs, second is empty
        
        async with scraper:
            results = await scraper.search_jobs(
                keywords=["marketing junior"],
                location="Vietnam",
                max_pages=2
            )
            
        # Should only return the marketing junior job
        assert len(results) == 1
        assert results[0].title == "Marketing Junior Executive"
        assert mock_scrape_page.call_count == 2
        
    @pytest.mark.asyncio
    async def test_scrape_search_page_url_construction(self, scraper):
        """Test search URL construction."""
        with patch('app.scrapers.indeed.IndeedScraper.make_request') as mock_request:
            mock_response = AsyncMock()
            mock_response.text.return_value = "<html><body></body></html>"
            mock_request.return_value.__aenter__.return_value = mock_response
            
            async with scraper:
                await scraper._scrape_search_page("marketing junior", "Vietnam", 10)
                
            # Verify the request was made with correct parameters
            call_args = mock_request.call_args
            url = call_args[0][0]
            
            assert "q=marketing+junior" in url
            assert "l=Vietnam" in url
            assert "start=10" in url
            assert "sort=date" in url
            
    def test_extract_job_from_card_basic(self, scraper):
        """Test basic job extraction from HTML card."""
        # Create mock HTML card
        html = '''
        <div class="job_seen_beacon">
            <h2 class="jobTitle">
                <a data-jk="123abc" href="/jobs?jk=123abc">
                    <span title="Marketing Junior Executive">Marketing Junior Executive</span>
                </a>
            </h2>
            <span class="companyName">Test Marketing Company</span>
            <div class="companyLocation">Ho Chi Minh City</div>
            <div class="summary">Looking for marketing professionals...</div>
            <span class="salaryText">10-15 triệu VND</span>
            <span class="date">2 days ago</span>
        </div>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        card = soup.find('div', class_='job_seen_beacon')
        
        # Test extraction (this would normally be async, but we'll test the parsing logic)
        # We need to mock the async parts
        with patch.object(scraper, '_get_job_description', return_value=None):
            import asyncio
            job_data = asyncio.run(scraper._extract_job_from_card(card))
            
        assert job_data is not None
        assert job_data.external_id == "indeed_123abc"
        assert job_data.title == "Marketing Junior Executive"
        assert job_data.company_name == "Test Marketing Company"
        assert job_data.location == "Ho Chi Minh City"
        assert job_data.source == JobSource.INDEED
        
    def test_parse_salary_range(self, scraper):
        """Test salary parsing functionality."""
        # Test range format
        min_sal, max_sal = scraper._parse_salary("10-15 triệu VND")
        assert min_sal == 10_000_000
        assert max_sal == 15_000_000
        
        # Test single value
        min_sal, max_sal = scraper._parse_salary("12 triệu VND")
        assert min_sal == 12_000_000
        assert max_sal == 12_000_000
        
        # Test with commas
        min_sal, max_sal = scraper._parse_salary("8,000,000 - 12,000,000 VND")
        assert min_sal == 8_000_000
        assert max_sal == 12_000_000
        
        # Test invalid format
        min_sal, max_sal = scraper._parse_salary("Competitive salary")
        assert min_sal is None
        assert max_sal is None
        
        # Test empty string
        min_sal, max_sal = scraper._parse_salary("")
        assert min_sal is None
        assert max_sal is None
        
    def test_parse_date_relative(self, scraper):
        """Test date parsing for relative dates."""
        now = datetime.utcnow()
        
        # Test "today" variants
        parsed = scraper._parse_date("today")
        assert parsed is not None
        assert abs((now - parsed).total_seconds()) < 1  # Within 1 second
        
        parsed = scraper._parse_date("just posted")
        assert parsed is not None
        assert abs((now - parsed).total_seconds()) < 1  # Within 1 second
        
        # Test "yesterday"
        parsed = scraper._parse_date("yesterday")
        assert parsed is not None
        assert abs((now - parsed).days - 1) <= 1  # Allow 1 day tolerance
        
        # Test days ago
        parsed = scraper._parse_date("3 days ago")
        assert parsed is not None
        assert abs((now - parsed).days - 3) <= 1  # Allow 1 day tolerance
        
        # Test weeks ago
        parsed = scraper._parse_date("2 weeks ago")
        assert parsed is not None
        assert abs((now - parsed).days - 14) <= 1  # Allow 1 day tolerance
        
        # Test months ago
        parsed = scraper._parse_date("1 month ago")
        assert parsed is not None
        assert abs((now - parsed).days - 30) <= 2  # Allow 2 day tolerance
        
        # Test invalid format
        parsed = scraper._parse_date("invalid date")
        assert parsed is None
        
        # Test empty string
        parsed = scraper._parse_date("")
        assert parsed is None
        
    @pytest.mark.asyncio
    async def test_get_job_description_success(self, scraper):
        """Test successful job description fetching."""
        mock_html = '''
        <html>
            <div id="jobDescriptionText">
                <p>We are looking for a marketing professional...</p>
                <ul>
                    <li>Create marketing campaigns</li>
                    <li>Analyze market trends</li>
                </ul>
            </div>
        </html>
        '''
        
        with patch.object(scraper, 'make_request') as mock_request:
            mock_response = AsyncMock()
            mock_response.text.return_value = mock_html
            mock_request.return_value.__aenter__.return_value = mock_response
            
            async with scraper:
                description = await scraper._get_job_description("https://example.com/job")
                
            assert description is not None
            assert "marketing professional" in description
            assert "Create marketing campaigns" in description
            
    @pytest.mark.asyncio
    async def test_get_job_description_failure(self, scraper):
        """Test job description fetching failure."""
        with patch.object(scraper, 'make_request') as mock_request:
            mock_request.side_effect = Exception("Network error")
            
            async with scraper:
                description = await scraper._get_job_description("https://example.com/job")
                
            assert description is None
            
    def test_marketing_junior_job_detection_specific(self, scraper):
        """Test Indeed-specific marketing junior job detection."""
        # Valid marketing junior jobs
        assert scraper.is_marketing_junior_job(
            "Marketing Executive - Fresh Graduate Welcome",
            "We welcome fresh graduates to join our marketing team..."
        )
        
        assert scraper.is_marketing_junior_job(
            "Digital Marketing Assistant",
            "Entry level position in digital marketing with training provided..."
        )
        
        assert scraper.is_marketing_junior_job(
            "Social Media Marketing Intern",
            "Internship program for marketing students and fresh graduates..."
        )
        
        # Invalid cases
        assert not scraper.is_marketing_junior_job(
            "Marketing Manager",
            "5+ years experience in marketing management required..."
        )
        
        assert not scraper.is_marketing_junior_job(
            "Junior Software Developer",
            "Entry level programming position for fresh graduates..."
        )
        
    @pytest.mark.asyncio
    async def test_search_jobs_error_handling(self, scraper):
        """Test error handling during job search."""
        with patch.object(scraper, '_scrape_search_page') as mock_scrape:
            mock_scrape.side_effect = ScrapingError("Network error")
            
            async with scraper:
                results = await scraper.search_jobs(
                    keywords=["marketing"],
                    max_pages=2
                )
                
            # Should return empty list on error
            assert results == []
            
    def test_extract_job_from_card_missing_elements(self, scraper):
        """Test job extraction with missing HTML elements."""
        # Card with minimal information
        html = '''
        <div class="job_seen_beacon">
            <h2 class="jobTitle">
                <a data-jk="123abc">
                    <span>Marketing Role</span>
                </a>
            </h2>
        </div>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        card = soup.find('div', class_='job_seen_beacon')
        
        with patch.object(scraper, '_get_job_description', return_value=None):
            import asyncio
            job_data = asyncio.run(scraper._extract_job_from_card(card))
            
        assert job_data is not None
        assert job_data.external_id == "indeed_123abc"
        assert job_data.title == "Marketing Role"
        assert job_data.company_name == "Unknown Company"  # Default
        assert job_data.location == "Vietnam"  # Default
        
    def test_extract_job_from_card_no_id(self, scraper):
        """Test job extraction when no ID is available."""
        # Card without data-jk or job URL
        html = '''
        <div class="job_seen_beacon">
            <h2 class="jobTitle">
                <span>Marketing Role</span>
            </h2>
        </div>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        card = soup.find('div', class_='job_seen_beacon')
        
        with patch.object(scraper, '_get_job_description', return_value=None):
            import asyncio
            job_data = asyncio.run(scraper._extract_job_from_card(card))
            
        # Should return None when no ID can be extracted
        assert job_data is None