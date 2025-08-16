from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base
import enum


class JobSource(str, enum.Enum):
    INDEED = "indeed"
    LINKEDIN = "linkedin"


class JobType(str, enum.Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class ExperienceLevel(str, enum.Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, nullable=False)
    title = Column(String(500), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    description = Column(Text, nullable=False)
    location = Column(String(255), index=True)
    url = Column(String(767), unique=True, nullable=False)  # 767 chars * 4 bytes = 3068 bytes < 3072 limit
    source = Column(Enum(JobSource), nullable=False, index=True)
    job_type = Column(Enum(JobType), nullable=True)
    experience_level = Column(Enum(ExperienceLevel), nullable=True, index=True)
    salary_min = Column(Numeric(10, 2), nullable=True)
    salary_max = Column(Numeric(10, 2), nullable=True)
    salary_currency = Column(String(3), default="VND")
    posted_date = Column(DateTime(timezone=True), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    company = relationship("Company", back_populates="jobs")

    def __repr__(self):
        return f"<Job(id={self.id}, title='{self.title}', company_id={self.company_id}, experience_level='{self.experience_level}')>"