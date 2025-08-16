"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base, get_db
from app.main import app
from app.models import Company, Job

# Create test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client with database override"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_company(db):
    """Create a sample company for testing"""
    company = Company(
        name="Test Marketing Agency",
        website="https://test-agency.com",
        industry="Marketing & Advertising"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture
def sample_job(db, sample_company):
    """Create a sample job for testing"""
    job = Job(
        external_id="test_job_001",
        title="Junior Marketing Executive",
        company_id=sample_company.id,
        description="Test job description for marketing position",
        location="Ho Chi Minh City",
        url="https://test.com/job1",
        source="indeed",
        job_type="full-time",
        experience_level="junior",
        salary_min=8000000,
        salary_max=12000000,
        salary_currency="VND",
        is_active=True
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job