# Job Scraper Backend - Marketing Junior Focus

FastAPI backend for the Job Scraper application, specialized in finding Marketing Junior positions in Vietnam.

## Features Implemented

- ✅ Simplified database schema (jobs + companies only)
- ✅ FastAPI with automatic API documentation
- ✅ SQLAlchemy models for Job and Company
- ✅ MySQL database with Docker support
- ✅ Health check endpoints
- ✅ Database statistics endpoint
- ✅ Unit and integration tests with coverage
- ✅ GitHub Actions CI/CD pipeline
- ✅ Connection pooling for better performance
- ✅ CORS middleware for frontend integration

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM for database operations
- **MySQL 8.0** - Database
- **Docker & Docker Compose** - Containerization
- **Pytest** - Testing framework

## Quick Start

### Using Docker Compose (Recommended)

1. Start all services:
```bash
docker-compose up -d
```

2. Check services:
```bash
docker-compose ps
```

3. View logs:
```bash
docker-compose logs -f backend
```

4. Access the API:
```bash
open http://localhost:8000/docs
```

### Local Development

1. Start MySQL (using Docker):
```bash
docker-compose up -d mysql
```

2. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing
```

4. Configure environment:
```bash
cp .env.example .env
# Update .env if needed
```

5. Run the application:
```bash
python run.py
# Or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- **API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: GET http://localhost:8000/api/health
- **Database Health**: GET http://localhost:8000/api/health/db
- **Database Stats**: GET http://localhost:8000/api/database/stats
- **Initialize Sample Data**: POST http://localhost:8000/api/database/init

## Database Schema

### Companies Table
```sql
CREATE TABLE companies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    website VARCHAR(500),
    industry VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP
);
```

### Jobs Table
```sql
CREATE TABLE jobs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    external_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    company_id INT REFERENCES companies(id),
    description TEXT NOT NULL,
    location VARCHAR(255),
    url VARCHAR(1000) UNIQUE NOT NULL,
    source ENUM('indeed', 'linkedin') NOT NULL,
    job_type ENUM('full-time', 'part-time', 'contract', 'internship'),
    experience_level ENUM('entry', 'junior', 'mid', 'senior'),
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    salary_currency VARCHAR(3) DEFAULT 'VND',
    posted_date DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP
);
```

## Testing

Run tests with coverage:
```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_models.py -v

# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── health.py      # Health check endpoints
│   │   └── database.py    # Database management endpoints
│   ├── core/
│   │   └── config.py      # Settings configuration
│   ├── database/
│   │   ├── session.py     # Database session management
│   │   └── init_db.py     # Database initialization
│   ├── models/
│   │   ├── company.py     # Company model
│   │   └── job.py         # Job model
│   └── main.py            # FastAPI application
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Test fixtures
├── requirements.txt       # Production dependencies
├── requirements-test.txt  # Test dependencies
├── Dockerfile            # Docker configuration
├── init.sql             # Database initialization SQL
└── run.py               # Application entry point
```

## Environment Variables

Create a `.env` file in the backend directory:
```env
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=jobuser
MYSQL_PASSWORD=jobpass
MYSQL_DATABASE=job_scraper

# API
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
```

## CI/CD Pipeline

GitHub Actions workflow runs on every push/PR:
1. **Linting**: Code quality checks with flake8
2. **Unit Tests**: Model and endpoint tests
3. **Integration Tests**: Database operation tests
4. **Coverage Report**: Minimum 70% coverage required
5. **Docker Build**: Verify container builds successfully

## Development Tips

1. **Database Migrations**: After model changes, recreate tables:
```python
from app.database.init_db import drop_all_tables, init_db
drop_all_tables()  # Caution: Drops all data
init_db()
```

2. **Sample Data**: Initialize database with test data:
```bash
curl -X POST http://localhost:8000/api/database/init
```

3. **View Database Stats**:
```bash
curl http://localhost:8000/api/database/stats | python -m json.tool
```

## Next Steps

After this PR is merged, the next implementations will be:
1. **PR #2**: Marketing-focused web scrapers for Indeed and LinkedIn
2. **PR #3**: Core API endpoints for jobs and companies with filtering
3. **PR #4**: React frontend setup with TypeScript