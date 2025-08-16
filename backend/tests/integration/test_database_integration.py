"""
Integration tests for database operations
"""
import pytest
from app.models import Company, Job, ExperienceLevel


class TestDatabaseIntegration:
    """Test database integration scenarios"""
    
    def test_create_job_with_company(self, db):
        """Test creating a job with associated company"""
        # Create company
        company = Company(
            name="Digital Marketing Co.",
            website="https://digital-marketing.vn",
            industry="Marketing"
        )
        db.add(company)
        db.commit()
        
        # Create job
        job = Job(
            external_id="test_integration_001",
            title="Junior Marketing Specialist",
            company_id=company.id,
            description="Join our marketing team",
            location="Hanoi",
            url="https://test.com/job",
            source="linkedin",
            job_type="full-time",
            experience_level="junior",
            salary_min=10000000,
            salary_max=15000000,
            is_active=True
        )
        db.add(job)
        db.commit()
        
        # Verify relationships
        assert job.company.name == "Digital Marketing Co."
        assert len(company.jobs) == 1
        assert company.jobs[0].title == "Junior Marketing Specialist"
    
    def test_filter_junior_marketing_jobs(self, db):
        """Test filtering for junior marketing positions"""
        # Create companies
        companies = [
            Company(name="Company A", industry="Marketing"),
            Company(name="Company B", industry="Technology"),
        ]
        for c in companies:
            db.add(c)
        db.commit()
        
        # Create various jobs
        jobs = [
            Job(
                external_id="job_001",
                title="Junior Marketing Executive",
                company_id=companies[0].id,
                description="Marketing role",
                location="HCMC",
                url="https://test.com/1",
                source="indeed",
                experience_level="junior",
                is_active=True
            ),
            Job(
                external_id="job_002",
                title="Senior Developer",
                company_id=companies[1].id,
                description="Tech role",
                location="HCMC",
                url="https://test.com/2",
                source="linkedin",
                experience_level="senior",
                is_active=True
            ),
            Job(
                external_id="job_003",
                title="Marketing Intern",
                company_id=companies[0].id,
                description="Entry level marketing",
                location="Hanoi",
                url="https://test.com/3",
                source="indeed",
                experience_level="entry",
                is_active=True
            ),
        ]
        for j in jobs:
            db.add(j)
        db.commit()
        
        # Query junior/entry level marketing jobs
        junior_jobs = db.query(Job).filter(
            Job.experience_level.in_([ExperienceLevel.ENTRY, ExperienceLevel.JUNIOR]),
            Job.title.contains("Marketing")
        ).all()
        
        assert len(junior_jobs) == 2
        assert all("Marketing" in job.title for job in junior_jobs)
        assert all(job.experience_level in ["entry", "junior"] for job in junior_jobs)
    
    def test_cascade_delete_behavior(self, db):
        """Test that deleting a company doesn't delete jobs (SET NULL)"""
        # Create company and job
        company = Company(name="Test Company", industry="Marketing")
        db.add(company)
        db.commit()
        
        job = Job(
            external_id="cascade_test",
            title="Test Job",
            company_id=company.id,
            description="Test",
            location="Test",
            url="https://test.com/cascade",
            source="indeed",
            is_active=True
        )
        db.add(job)
        db.commit()
        
        # Delete company
        db.delete(company)
        db.commit()
        
        # Job should still exist with null company_id
        job_after = db.query(Job).filter(Job.external_id == "cascade_test").first()
        assert job_after is not None
        assert job_after.company_id is None