# Testing Strategy

## Overview
We follow Test-Driven Development (TDD) principles with comprehensive unit and integration testing.

## Testing Stack
- **Framework**: pytest
- **Coverage**: pytest-cov (minimum 80% coverage)
- **Mocking**: pytest-mock
- **Async Testing**: pytest-asyncio
- **API Testing**: httpx
- **Database Testing**: pytest + SQLAlchemy test fixtures
- **CI/CD**: GitHub Actions

## Test Structure

```
backend/
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── unit/                    # Unit tests
│   │   ├── test_models.py
│   │   ├── test_scrapers.py
│   │   ├── test_services.py
│   │   └── test_utils.py
│   ├── integration/             # Integration tests
│   │   ├── test_api_jobs.py
│   │   ├── test_api_scraping.py
│   │   ├── test_api_stats.py
│   │   └── test_database.py
│   ├── e2e/                     # End-to-end tests
│   │   └── test_workflows.py
│   └── fixtures/                # Test data
│       ├── job_samples.json
│       └── company_samples.json
```

## Testing Principles

### 1. TDD Workflow
1. **Red**: Write a failing test
2. **Green**: Write minimal code to pass the test
3. **Refactor**: Improve code while keeping tests green

### 2. Test Naming Convention
```python
def test_should_<expected_behavior>_when_<condition>():
    """Test that <component> should <behavior> when <condition>."""
    pass
```

### 3. AAA Pattern
```python
def test_job_creation():
    # Arrange
    job_data = {"title": "Marketing Manager"}
    
    # Act
    job = create_job(job_data)
    
    # Assert
    assert job.title == "Marketing Manager"
```

## Test Categories

### Unit Tests
Test individual components in isolation.

```python
# tests/unit/test_models.py
import pytest
from app.models.job import Job

class TestJobModel:
    def test_should_create_job_with_valid_data(self):
        job = Job(
            title="Marketing Executive",
            company_id=1,
            description="Job description",
            url="https://example.com/job/123"
        )
        assert job.title == "Marketing Executive"
        assert job.is_active is True
    
    def test_should_raise_error_when_title_missing(self):
        with pytest.raises(ValueError):
            Job(company_id=1, description="Desc", url="https://...")
```

### Integration Tests
Test component interactions.

```python
# tests/integration/test_api_jobs.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_jobs_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/jobs")
        assert response.status_code == 200
        assert response.json()["success"] is True

@pytest.mark.asyncio
async def test_create_job_with_database(db_session):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/jobs", json={
            "title": "Test Job",
            "company": "Test Company"
        })
        assert response.status_code == 201
        
        # Verify in database
        job = db_session.query(Job).filter_by(title="Test Job").first()
        assert job is not None
```

### E2E Tests
Test complete user workflows.

```python
# tests/e2e/test_workflows.py
@pytest.mark.e2e
async def test_complete_scraping_workflow():
    # Trigger scraping
    session = await trigger_scraping("indeed", {"location": "Vietnam"})
    assert session.status == "running"
    
    # Wait for completion
    await wait_for_completion(session.id)
    
    # Verify jobs were scraped
    jobs = await get_jobs(source="indeed")
    assert len(jobs) > 0
    
    # Verify statistics updated
    stats = await get_statistics()
    assert stats.last_scraping is not None
```

## Fixtures

### Database Fixtures
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base

@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def sample_job():
    """Provide sample job data."""
    return {
        "title": "Marketing Manager",
        "company": "ABC Corp",
        "location": "Ho Chi Minh City",
        "description": "We are looking for...",
        "url": "https://example.com/job/123"
    }
```

### Mock Fixtures
```python
@pytest.fixture
def mock_scraper(mocker):
    """Mock scraper for testing."""
    mock = mocker.patch("app.scrapers.indeed.IndeedScraper")
    mock.return_value.scrape.return_value = [
        {"title": "Job 1", "url": "https://..."},
        {"title": "Job 2", "url": "https://..."}
    ]
    return mock
```

## Coverage Requirements

### Minimum Coverage
- Overall: 80%
- Core business logic: 90%
- API endpoints: 85%
- Database models: 80%
- Utilities: 70%

### Coverage Report
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

## Performance Testing

```python
# tests/performance/test_load.py
import pytest
from locust import HttpUser, task, between

class JobAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_jobs(self):
        self.client.get("/api/jobs")
    
    @task
    def search_jobs(self):
        self.client.get("/api/jobs?search=Marketing")
```

## Testing Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with markers
pytest -m "not e2e"  # Skip E2E tests
pytest -m "slow"      # Only slow tests

# Run in parallel
pytest -n auto

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test
          MYSQL_DATABASE: test_db
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run tests with coverage
        run: |
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Data Management

### Factory Pattern
```python
# tests/factories.py
import factory
from app.models import Job, Company

class CompanyFactory(factory.Factory):
    class Meta:
        model = Company
    
    name = factory.Faker("company")
    website = factory.Faker("url")

class JobFactory(factory.Factory):
    class Meta:
        model = Job
    
    title = factory.Faker("job")
    company = factory.SubFactory(CompanyFactory)
    description = factory.Faker("text")
    location = factory.Faker("city")
```

## Testing Best Practices

1. **Isolation**: Each test should be independent
2. **Clarity**: Test names should clearly describe what is being tested
3. **Speed**: Unit tests should be fast (<100ms)
4. **Deterministic**: Tests should always produce the same result
5. **Single Responsibility**: Each test should test one thing
6. **No Logic in Tests**: Tests should not contain conditionals or loops
7. **Use Fixtures**: Share common setup through fixtures
8. **Mock External Dependencies**: Don't make real HTTP calls or database connections in unit tests

## Continuous Improvement

- Review test coverage weekly
- Add tests for every bug fix
- Refactor tests when they become brittle
- Monitor test execution time
- Use mutation testing to verify test quality