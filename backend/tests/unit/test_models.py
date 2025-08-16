"""
Unit tests for database models
"""
import pytest
from datetime import datetime
from app.models import Company, Job, JobSource, JobType, ExperienceLevel


class TestCompanyModel:
    """Test Company model"""
    
    def test_create_company(self, db):
        """Test creating a company"""
        company = Company(
            name="FPT Corporation",
            website="https://fpt.com.vn",
            industry="Technology"
        )
        db.add(company)
        db.commit()
        
        assert company.id is not None
        assert company.name == "FPT Corporation"
        assert company.website == "https://fpt.com.vn"
        assert company.industry == "Technology"
        assert company.created_at is not None
    
    def test_company_repr(self, sample_company):
        """Test company string representation"""
        repr_str = repr(sample_company)
        assert "Test Marketing Agency" in repr_str
        assert "Marketing & Advertising" in repr_str


class TestJobModel:
    """Test Job model"""
    
    def test_create_job(self, db, sample_company):
        """Test creating a job"""
        job = Job(
            external_id="indeed_12345",
            title="Marketing Executive - Fresh Graduate",
            company_id=sample_company.id,
            description="Looking for fresh graduates...",
            location="Ho Chi Minh City",
            url="https://indeed.com/job/12345",
            source=JobSource.INDEED,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.ENTRY,
            salary_min=8000000,
            salary_max=12000000,
            salary_currency="VND",
            posted_date=datetime.utcnow(),
            is_active=True
        )
        db.add(job)
        db.commit()
        
        assert job.id is not None
        assert job.title == "Marketing Executive - Fresh Graduate"
        assert job.company_id == sample_company.id
        assert job.experience_level == ExperienceLevel.ENTRY
        assert job.salary_min == 8000000
        assert job.is_active is True
    
    def test_job_company_relationship(self, sample_job, sample_company):
        """Test job-company relationship"""
        assert sample_job.company.id == sample_company.id
        assert sample_job.company.name == sample_company.name
        assert sample_job in sample_company.jobs
    
    def test_job_repr(self, sample_job):
        """Test job string representation"""
        repr_str = repr(sample_job)
        assert "Junior Marketing Executive" in repr_str
        assert "JUNIOR" in repr_str
    
    def test_job_enums(self):
        """Test job enum values"""
        assert JobSource.INDEED.value == "indeed"
        assert JobSource.LINKEDIN.value == "linkedin"
        
        assert JobType.FULL_TIME.value == "full-time"
        assert JobType.INTERNSHIP.value == "internship"
        
        assert ExperienceLevel.ENTRY.value == "entry"
        assert ExperienceLevel.JUNIOR.value == "junior"