from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models import Job, Company, ExperienceLevel
from datetime import datetime

router = APIRouter(prefix="/api/database", tags=["database"])


@router.get("/stats")
async def get_database_stats(db: Session = Depends(get_db)):
    """Get database statistics for jobs and companies"""
    try:
        # Count total jobs
        total_jobs = db.query(func.count(Job.id)).scalar()
        active_jobs = db.query(func.count(Job.id)).filter(Job.is_active == True).scalar()  # noqa: E712
        
        # Count by experience level
        junior_jobs = db.query(func.count(Job.id)).filter(
            Job.experience_level.in_([ExperienceLevel.ENTRY, ExperienceLevel.JUNIOR])
        ).scalar()
        
        # Count companies
        total_companies = db.query(func.count(Company.id)).scalar()
        
        # Count by source
        indeed_jobs = db.query(func.count(Job.id)).filter(
            Job.source == "indeed").scalar()
        linkedin_jobs = db.query(func.count(Job.id)).filter(
            Job.source == "linkedin").scalar()
        
        return {
            "jobs": {
                "total": total_jobs,
                "active": active_jobs,
                "junior_level": junior_jobs,
                "by_source": {
                    "indeed": indeed_jobs,
                    "linkedin": linkedin_jobs
                }
            },
            "companies": {
                "total": total_companies
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/init")
async def initialize_database(db: Session = Depends(get_db)):
    """Initialize database with sample data for testing"""
    try:
        # Check if data already exists
        existing_jobs = db.query(func.count(Job.id)).scalar()
        if existing_jobs > 0:
            return {"message": "Database already contains data", "job_count": existing_jobs}
        
        # Create sample companies
        companies = [
            Company(name="ABC Marketing Agency", website="https://abc-marketing.vn", industry="Marketing & Advertising"),
            Company(name="Digital Ventures Vietnam", website="https://digitalventures.vn", industry="Technology"),
            Company(name="Creative Solutions Co.", website="https://creative-solutions.vn", industry="Marketing & Advertising"),
        ]
        
        for company in companies:
            db.add(company)
        db.commit()
        
        # Create sample jobs
        jobs = [
            Job(
                external_id="sample_001",
                title="Marketing Executive - Fresh Graduate",
                company_id=1,
                description="Looking for fresh graduates passionate about marketing...",
                location="Ho Chi Minh City",
                url="https://example.com/job1",
                source="indeed",
                job_type="full-time",
                experience_level="entry",
                salary_min=8000000,
                salary_max=12000000,
                posted_date=datetime.utcnow(),
                is_active=True
            ),
            Job(
                external_id="sample_002",
                title="Junior Digital Marketing Specialist",
                company_id=2,
                description="Join our digital marketing team...",
                location="Hanoi",
                url="https://example.com/job2",
                source="linkedin",
                job_type="full-time",
                experience_level="junior",
                salary_min=10000000,
                salary_max=15000000,
                posted_date=datetime.utcnow(),
                is_active=True
            ),
        ]
        
        for job in jobs:
            db.add(job)
        db.commit()
        
        return {
            "message": "Database initialized with sample data",
            "companies_created": len(companies),
            "jobs_created": len(jobs)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to initialize database: {str(e)}")