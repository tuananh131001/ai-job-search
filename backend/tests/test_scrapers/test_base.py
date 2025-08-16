"""Tests for base scraper functionality."""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

import aiohttp
from fake_useragent import UserAgent

from app.scrapers.base import BaseScraper, JobData, ScrapingError, RateLimitError
from app.models import JobSource


class TestBaseScraper:
    """Test suite for BaseScraper abstract class functionality."""
    
    @pytest.fixture
    def mock_scraper(self):
        """Create a concrete implementation of BaseScraper for testing."""
        
        class ConcreteScraper(BaseScraper):
            async def search_jobs(self, keywords, location="Vietnam", max_pages=5):
                return []
                
            def get_job_source(self):
                return JobSource.INDEED
                
        return ConcreteScraper()
        
    @pytest.mark.asyncio
    async def test_scraper_initialization(self, mock_scraper):
        """Test scraper initialization with default parameters."""
        assert mock_scraper.requests_per_minute == 30
        assert mock_scraper.timeout == 30
        assert mock_scraper.max_retries == 3
        assert mock_scraper.retry_delay == 1.0
        assert mock_scraper.session is None
        assert isinstance(mock_scraper.ua, UserAgent)
        
    @pytest.mark.asyncio
    async def test_scraper_custom_initialization(self):
        """Test scraper initialization with custom parameters."""
        
        class CustomScraper(BaseScraper):
            async def search_jobs(self, keywords, location="Vietnam", max_pages=5):
                return []
                
            def get_job_source(self):
                return JobSource.LINKEDIN
                
        scraper = CustomScraper(
            requests_per_minute=10,
            timeout=60,
            max_retries=5,
            retry_delay=2.5,
        )
        
        assert scraper.requests_per_minute == 10
        assert scraper.timeout == 60
        assert scraper.max_retries == 5
        assert scraper.retry_delay == 2.5
        
    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_scraper):
        """Test async context manager functionality."""
        async with mock_scraper as scraper:
            assert scraper.session is not None
            assert isinstance(scraper.session, aiohttp.ClientSession)
            
        # Session should be closed after context exit
        assert scraper.session is None or scraper.session.closed
        
    @pytest.mark.asyncio
    async def test_session_management(self, mock_scraper):
        """Test session creation and cleanup."""
        # Initially no session
        assert mock_scraper.session is None
        
        # Start session
        await mock_scraper.start_session()
        assert mock_scraper.session is not None
        assert isinstance(mock_scraper.session, aiohttp.ClientSession)
        
        # Close session
        await mock_scraper.close_session()
        assert mock_scraper.session is None
        
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.request')
    async def test_make_request_success(self, mock_request, mock_scraper):
        """Test successful HTTP request."""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_request.return_value = mock_response
        
        async with mock_scraper:
            response = await mock_scraper.make_request('https://example.com')
            assert response.status == 200
            
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.request')
    async def test_make_request_rate_limit(self, mock_request, mock_scraper):
        """Test rate limit handling."""
        # Mock rate limited response
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {'Retry-After': '1'}
        mock_response.__aenter__.return_value = mock_response
        mock_request.return_value = mock_response
        
        async with mock_scraper:
            with patch('asyncio.sleep') as mock_sleep:
                try:
                    await mock_scraper.make_request('https://example.com')
                except ScrapingError:
                    pass  # Expected after retries
                # Should have called sleep for rate limiting
                mock_sleep.assert_called()
                
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.request')
    async def test_make_request_retry_logic(self, mock_request, mock_scraper):
        """Test retry logic for failed requests."""
        # Mock failed response that should trigger retries
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__.return_value = mock_response
        mock_request.return_value = mock_response
        
        async with mock_scraper:
            with patch('asyncio.sleep') as mock_sleep:
                with pytest.raises(ScrapingError):
                    await mock_scraper.make_request('https://example.com')
                # Should have retried and slept between retries
                assert mock_sleep.call_count == mock_scraper.max_retries
                
    def test_is_marketing_junior_job(self, mock_scraper):
        """Test marketing junior job detection."""
        # Positive cases
        assert mock_scraper.is_marketing_junior_job(
            "Marketing Junior Executive",
            "We are looking for a junior marketing professional..."
        )
        
        assert mock_scraper.is_marketing_junior_job(
            "Digital Marketing Assistant",
            "Entry level position for fresh graduates in marketing..."
        )
        
        assert mock_scraper.is_marketing_junior_job(
            "Social Media Marketing Trainee",
            "Internship program for marketing students..."
        )
        
        # Negative cases
        assert not mock_scraper.is_marketing_junior_job(
            "Senior Software Engineer",
            "5+ years experience in software development..."
        )
        
        assert not mock_scraper.is_marketing_junior_job(
            "Marketing Director",
            "Lead our marketing team with 10+ years experience..."
        )
        
        assert not mock_scraper.is_marketing_junior_job(
            "Junior Developer",
            "Programming position for fresh graduates..."
        )
        
    def test_extract_experience_level(self, mock_scraper):
        """Test experience level extraction."""
        # Entry level
        assert mock_scraper.extract_experience_level(
            "Marketing Intern",
            "Fresh graduate position..."
        ) == "entry"
        
        assert mock_scraper.extract_experience_level(
            "Marketing Trainee",
            "Training program for new graduates..."
        ) == "entry"
        
        # Junior level
        assert mock_scraper.extract_experience_level(
            "Junior Marketing Executive",
            "0-2 years experience required..."
        ) == "junior"
        
        assert mock_scraper.extract_experience_level(
            "Marketing Specialist",
            "Junior level position with 0-1 year experience..."
        ) == "junior"
        
        # No clear level
        assert mock_scraper.extract_experience_level(
            "Marketing Professional",
            "Marketing role with competitive salary..."
        ) is None
        
    def test_normalize_url(self, mock_scraper):
        """Test URL normalization."""
        base_url = "https://example.com"
        
        # Absolute URLs should remain unchanged
        assert mock_scraper.normalize_url(
            "https://other.com/job",
            base_url
        ) == "https://other.com/job"
        
        # Protocol-relative URLs
        assert mock_scraper.normalize_url(
            "//other.com/job",
            base_url
        ) == "https://other.com/job"
        
        # Relative URLs
        assert mock_scraper.normalize_url(
            "/job/123",
            base_url
        ) == "https://example.com/job/123"
        
        assert mock_scraper.normalize_url(
            "job/123",
            base_url
        ) == "https://example.com/job/123"
        
        # Empty URL
        assert mock_scraper.normalize_url("", base_url) == ""
        assert mock_scraper.normalize_url(None, base_url) == ""
        
    def test_clean_text(self, mock_scraper):
        """Test text cleaning functionality."""
        # Basic cleaning
        assert mock_scraper.clean_text("  Hello   World  ") == "Hello World"
        
        # Newlines and tabs
        assert mock_scraper.clean_text("Hello\n\tWorld\r\n") == "Hello World"
        
        # Multiple spaces
        assert mock_scraper.clean_text("Hello     World") == "Hello World"
        
        # Empty strings
        assert mock_scraper.clean_text("") == ""
        assert mock_scraper.clean_text(None) == ""
        
        # Complex text
        assert mock_scraper.clean_text(
            "  Marketing\n\n  Junior   Position\t\t"
        ) == "Marketing Junior Position"


class TestJobData:
    """Test suite for JobData dataclass."""
    
    def test_job_data_creation(self):
        """Test JobData creation with required fields."""
        job_data = JobData(
            external_id="test_123",
            title="Marketing Junior",
            company_name="Test Company",
            description="Test description",
            location="Vietnam",
            url="https://example.com/job",
            source=JobSource.INDEED,
        )
        
        assert job_data.external_id == "test_123"
        assert job_data.title == "Marketing Junior"
        assert job_data.company_name == "Test Company"
        assert job_data.description == "Test description"
        assert job_data.location == "Vietnam"
        assert job_data.url == "https://example.com/job"
        assert job_data.source == JobSource.INDEED
        assert job_data.salary_currency == "VND"  # Default
        assert job_data.is_active is True  # Default
        
    def test_job_data_with_optional_fields(self):
        """Test JobData creation with optional fields."""
        posted_date = datetime.utcnow()
        
        job_data = JobData(
            external_id="test_123",
            title="Marketing Junior",
            company_name="Test Company",
            description="Test description",
            location="Vietnam",
            url="https://example.com/job",
            source=JobSource.LINKEDIN,
            job_type="part-time",
            experience_level="junior",
            salary_min=10000000.0,
            salary_max=15000000.0,
            salary_currency="USD",
            posted_date=posted_date,
            is_active=False,
        )
        
        assert job_data.job_type == "part-time"
        assert job_data.experience_level == "junior"
        assert job_data.salary_min == 10000000.0
        assert job_data.salary_max == 15000000.0
        assert job_data.salary_currency == "USD"
        assert job_data.posted_date == posted_date
        assert job_data.is_active is False


class TestScrapingExceptions:
    """Test suite for custom scraping exceptions."""
    
    def test_scraping_error(self):
        """Test ScrapingError exception."""
        error = ScrapingError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
        
    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, ScrapingError)
        assert isinstance(error, Exception)