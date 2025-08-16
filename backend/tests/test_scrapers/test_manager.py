"""Tests for scraping manager functionality."""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.scrapers.manager import ScrapingManager
from app.scrapers.base import JobData, ScrapingError
from app.models import Job, Company, JobSource, ExperienceLevel


class TestScrapingManager:
    """Test suite for ScrapingManager."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return Mock(spec=Session)
        
    @pytest.fixture
    def manager(self, mock_db_session):
        """Create ScrapingManager instance for testing."""
        return ScrapingManager(db_session=mock_db_session)
        
    @pytest.fixture
    def sample_job_data(self):
        """Create sample JobData for testing."""
        return [
            JobData(
                external_id="indeed_123",
                title="Marketing Junior Executive",
                company_name="Test Marketing Co.",
                description="Great marketing opportunity for juniors...",
                location="Ho Chi Minh City",
                url="https://vn.indeed.com/job/123",
                source=JobSource.INDEED,
                experience_level="junior",
                salary_min=10_000_000,
                salary_max=15_000_000,
                posted_date=datetime.utcnow(),
            ),
            JobData(
                external_id="linkedin_456",
                title="Digital Marketing Specialist",
                company_name="Digital Agency Ltd.",
                description="Entry level digital marketing role...",
                location="Hanoi",
                url="https://linkedin.com/job/456",
                source=JobSource.LINKEDIN,
                experience_level="entry",
                salary_min=8_000_000,
                salary_max=12_000_000,
                posted_date=datetime.utcnow(),
            ),
        ]
        
    def test_manager_initialization(self, manager, mock_db_session):
        """Test manager initialization."""
        assert manager.db_session == mock_db_session
        assert 'indeed' in manager.scrapers
        assert 'linkedin' in manager.scrapers
        assert len(manager.default_keywords) > 0
        assert 'marketing junior' in manager.default_keywords
        
    def test_manager_initialization_without_session(self):
        """Test manager initialization without database session."""
        manager = ScrapingManager()
        assert manager.db_session is None
        assert 'indeed' in manager.scrapers
        assert 'linkedin' in manager.scrapers
        
    @pytest.mark.asyncio
    async def test_scrape_all_sources_success(self, manager, sample_job_data):
        """Test successful scraping from all sources."""
        with patch.object(manager, '_scrape_source') as mock_scrape:
            # Mock scrape results
            mock_scrape.side_effect = [
                (sample_job_data[:1], {'jobs_found': 1, 'success': True}),  # Indeed
                (sample_job_data[1:], {'jobs_found': 1, 'success': True}),  # LinkedIn
            ]
            
            with patch.object(manager, '_save_jobs_to_db', return_value=2):
                results = await manager.scrape_all_sources(
                    keywords=["marketing junior"],
                    max_pages_per_source=2
                )
                
        assert results['total_jobs_found'] == 2
        assert results['unique_jobs'] == 2
        assert results['jobs_saved'] == 2
        assert len(results['source_statistics']) == 2
        assert len(results['errors']) == 0
        assert 'indeed' in results['source_statistics']
        assert 'linkedin' in results['source_statistics']
        
    @pytest.mark.asyncio
    async def test_scrape_all_sources_with_errors(self, manager, sample_job_data):
        """Test scraping with some sources failing."""
        with patch.object(manager, '_scrape_source') as mock_scrape:
            # Mock one successful, one failed
            mock_scrape.side_effect = [
                (sample_job_data[:1], {'jobs_found': 1, 'success': True}),  # Indeed success
                Exception("LinkedIn scraping failed"),  # LinkedIn failure
            ]
            
            with patch.object(manager, '_save_jobs_to_db', return_value=1):
                results = await manager.scrape_all_sources(
                    keywords=["marketing junior"],
                    sources=['indeed', 'linkedin']
                )
                
        assert results['total_jobs_found'] == 1
        assert results['unique_jobs'] == 1
        assert results['jobs_saved'] == 1
        assert len(results['errors']) == 1
        assert 'linkedin: LinkedIn scraping failed' in results['errors']
        
    @pytest.mark.asyncio
    async def test_scrape_source_success(self, manager, sample_job_data):
        """Test successful single source scraping."""
        # Mock the scrapers in the manager instance
        manager.scrapers['indeed'] = Mock()
        
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.search_jobs.return_value = sample_job_data[:1]
        mock_instance.is_marketing_junior_job.return_value = True
        manager.scrapers['indeed'].return_value = mock_instance
        
        jobs, stats = await manager._scrape_source(
            source='indeed',
            keywords=['marketing junior'],
            location='Vietnam',
            max_pages=2
        )
        
        assert len(jobs) == 1
        assert jobs[0].title == "Marketing Junior Executive"
        assert stats['success'] is True
        assert stats['jobs_found'] == 1
        assert 'start_time' in stats
        assert 'end_time' in stats
        
    @pytest.mark.asyncio
    async def test_scrape_source_failure(self, manager):
        """Test single source scraping failure."""
        # Mock the scrapers in the manager instance
        manager.scrapers['indeed'] = Mock()
        
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.search_jobs.side_effect = Exception("Scraping failed")
        manager.scrapers['indeed'].return_value = mock_instance
        
        with pytest.raises(ScrapingError):
            await manager._scrape_source(
                source='indeed',
                keywords=['marketing junior'],
                location='Vietnam',
                max_pages=2
            )
                
    def test_deduplicate_jobs_by_url(self, manager, sample_job_data):
        """Test job deduplication by URL."""
        # Create duplicate job with same URL
        duplicate_job = JobData(
            external_id="different_id",
            title="Different Title",
            company_name="Different Company",
            description="Different description",
            location="Different Location",
            url=sample_job_data[0].url,  # Same URL as first job
            source=JobSource.LINKEDIN,
        )
        
        jobs_with_duplicates = sample_job_data + [duplicate_job]
        unique_jobs = manager._deduplicate_jobs(jobs_with_duplicates)
        
        # Should remove the duplicate based on URL
        assert len(unique_jobs) == 2
        urls = [job.url for job in unique_jobs]
        assert len(set(urls)) == 2
        
    def test_deduplicate_jobs_by_external_id(self, manager):
        """Test job deduplication by external ID when URL is missing."""
        jobs = [
            JobData(
                external_id="same_id",
                title="Job 1",
                company_name="Company 1",
                description="Description 1",
                location="Location 1",
                url="",  # No URL
                source=JobSource.INDEED,
            ),
            JobData(
                external_id="same_id",  # Same external ID
                title="Job 2",
                company_name="Company 2",
                description="Description 2",
                location="Location 2",
                url="",  # No URL
                source=JobSource.LINKEDIN,
            ),
        ]
        
        unique_jobs = manager._deduplicate_jobs(jobs)
        
        # Should keep only one job
        assert len(unique_jobs) == 1
        
    @pytest.mark.asyncio
    async def test_save_jobs_to_db_success(self, manager, mock_db_session, sample_job_data):
        """Test successful job saving to database."""
        # Mock company finding/creation
        mock_company = Mock()
        mock_company.id = 1
        mock_company.name = "Test Company"
        
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_company,  # Company exists
            None,  # Job doesn't exist
            mock_company,  # Company exists for second job
            None,  # Second job doesn't exist
        ]
        
        with patch.object(manager, '_create_job_from_data') as mock_create:
            mock_create.return_value = Mock(spec=Job)
            
            saved_count = await manager._save_jobs_to_db(sample_job_data)
            
        assert saved_count == 2
        assert mock_create.call_count == 2
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        
    @pytest.mark.asyncio
    async def test_save_jobs_to_db_with_existing_jobs(self, manager, mock_db_session, sample_job_data):
        """Test saving jobs when some already exist in database."""
        mock_company = Mock()
        mock_company.id = 1
        
        existing_job = Mock(spec=Job)
        existing_job.id = 1
        
        # Mock database queries - first job exists, second doesn't
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_company,  # Company exists
            existing_job,  # Job exists
            mock_company,  # Company exists for second job
            None,  # Second job doesn't exist
        ]
        
        with patch.object(manager, '_update_job_from_data') as mock_update:
            with patch.object(manager, '_create_job_from_data') as mock_create:
                mock_create.return_value = Mock(spec=Job)
                
                saved_count = await manager._save_jobs_to_db(sample_job_data)
                
        assert saved_count == 2
        mock_update.assert_called_once()
        mock_create.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_save_jobs_to_db_integrity_error(self, manager, mock_db_session, sample_job_data):
        """Test handling of integrity errors during job saving."""
        mock_company = Mock()
        mock_company.id = 1
        
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_company,  # Company exists
            None,  # Job doesn't exist
        ]
        
        # Mock integrity error on add
        mock_db_session.add.side_effect = IntegrityError("Duplicate key", None, None)
        
        with patch.object(manager, '_create_job_from_data') as mock_create:
            mock_create.return_value = Mock(spec=Job)
            
            saved_count = await manager._save_jobs_to_db(sample_job_data[:1])
            
        # Should handle the error and continue
        assert saved_count == 0
        mock_db_session.rollback.assert_called()
        
    def test_find_or_create_company_existing(self, manager, mock_db_session):
        """Test finding existing company."""
        existing_company = Mock(spec=Company)
        existing_company.id = 1
        existing_company.name = "Existing Company"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_company
        
        company = manager._find_or_create_company("Existing Company")
        
        assert company == existing_company
        mock_db_session.add.assert_not_called()
        
    def test_find_or_create_company_new(self, manager, mock_db_session):
        """Test creating new company."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Use the actual Company class but mock the database operations
        from app.models import Company
        
        company = manager._find_or_create_company("New Company", "Tech")
        
        assert company.name == "New Company"
        assert company.industry == "Tech"
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()
        
    def test_create_job_from_data(self, manager, sample_job_data):
        """Test creating Job instance from JobData."""
        job_data = sample_job_data[0]
        company_id = 1
        
        # Use the actual Job class
        from app.models import Job
        
        result = manager._create_job_from_data(job_data, company_id)
        
        assert isinstance(result, Job)
        assert result.external_id == job_data.external_id
        assert result.title == job_data.title
        assert result.company_id == company_id
        assert result.description == job_data.description
        assert result.location == job_data.location
        assert result.url == job_data.url
        assert result.source == job_data.source
        assert result.job_type == job_data.job_type
        assert result.experience_level == job_data.experience_level
        assert result.salary_min == job_data.salary_min
        assert result.salary_max == job_data.salary_max
        assert result.salary_currency == job_data.salary_currency
        assert result.posted_date == job_data.posted_date
        assert result.is_active == job_data.is_active
        
    def test_update_job_from_data(self, manager, sample_job_data):
        """Test updating existing Job with new data."""
        job_data = sample_job_data[0]
        company_id = 2
        
        existing_job = Mock(spec=Job)
        existing_job.id = 1
        
        manager._update_job_from_data(existing_job, job_data, company_id)
        
        assert existing_job.title == job_data.title
        assert existing_job.company_id == company_id
        assert existing_job.description == job_data.description
        assert existing_job.location == job_data.location
        assert existing_job.job_type == job_data.job_type
        assert existing_job.experience_level == job_data.experience_level
        assert existing_job.salary_min == job_data.salary_min
        assert existing_job.salary_max == job_data.salary_max
        assert existing_job.salary_currency == job_data.salary_currency
        assert existing_job.posted_date == job_data.posted_date
        assert existing_job.is_active == job_data.is_active
        
    @pytest.mark.asyncio
    async def test_get_scraping_status(self, manager):
        """Test getting scraper status information."""
        with patch('app.scrapers.indeed.IndeedScraper') as MockIndeedScraper:
            with patch('app.scrapers.manager.LinkedInScraper') as MockLinkedInScraper:
                # Mock successful health checks
                mock_indeed = AsyncMock()
                mock_indeed.__aenter__.return_value = mock_indeed
                mock_indeed.requests_per_minute = 20
                MockIndeedScraper.return_value = mock_indeed
                
                mock_linkedin = AsyncMock()
                mock_linkedin.__aenter__.return_value = mock_linkedin
                mock_linkedin.requests_per_minute = 10
                MockLinkedInScraper.return_value = mock_linkedin
                
                status = await manager.get_scraping_status()
                
        assert 'available_scrapers' in status
        assert 'indeed' in status['available_scrapers']
        assert 'linkedin' in status['available_scrapers']
        assert 'default_keywords' in status
        assert 'scraper_health' in status
        assert status['scraper_health']['indeed']['status'] == 'healthy'
        assert status['scraper_health']['linkedin']['status'] == 'healthy'
        
    @pytest.mark.asyncio
    async def test_get_scraping_status_with_unhealthy_scraper(self, manager):
        """Test getting scraper status with unhealthy scraper."""
        # Mock the scrapers in the manager instance
        mock_indeed_class = Mock()
        mock_linkedin_class = Mock()
        
        # Indeed success
        mock_indeed = AsyncMock()
        mock_indeed.__aenter__.return_value = mock_indeed
        mock_indeed.__aexit__.return_value = None
        mock_indeed.requests_per_minute = 20
        mock_indeed_class.return_value = mock_indeed
        
        # LinkedIn failure
        mock_linkedin_class.side_effect = Exception("Connection failed")
        
        manager.scrapers = {
            'indeed': mock_indeed_class,
            'linkedin': mock_linkedin_class
        }
        
        status = await manager.get_scraping_status()
        
        assert status['scraper_health']['indeed']['status'] == 'healthy'
        assert status['scraper_health']['linkedin']['status'] == 'unhealthy'
        assert 'error' in status['scraper_health']['linkedin']