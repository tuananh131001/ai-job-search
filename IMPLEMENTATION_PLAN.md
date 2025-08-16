# Job Scraper Application - Implementation Plan (Simplified)

## Overview
A focused job scraping application specifically targeting Marketing Junior positions in Vietnam from Indeed and LinkedIn.

## Tech Stack
- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18 with TypeScript
- **Database**: MySQL 8.0 (simplified schema: jobs + companies only)
- **Scraping**: BeautifulSoup4 + Requests
- **Task Queue**: APScheduler for automated scraping
- **Deployment**: Docker Compose for MySQL and local development

## Architecture
```
job-scraper/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   │   ├── job.py
│   │   │   └── company.py
│   │   ├── scrapers/
│   │   │   ├── indeed.py
│   │   │   └── linkedin.py
│   │   ├── api/
│   │   │   ├── jobs.py
│   │   │   ├── companies.py
│   │   │   └── stats.py
│   │   └── database/
│   │       └── connection.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.tsx
│   └── package.json
├── docs/
│   ├── database/
│   │   └── SCHEMA.md
│   └── api/
│       └── API_CONTRACT.md
└── docker-compose.yml
```

## Implementation Steps (Focused PRs)

### PR #1: Backend Foundation & Database Setup (~200 lines)
- Set up FastAPI project structure
- Create MySQL database with simplified schema (jobs + companies only)
- Implement database models using SQLAlchemy
- Create database connection and session management
- Add health check endpoint
- Docker Compose setup for MySQL

### PR #2: Marketing-Focused Scrapers (~300 lines)
- Create Indeed scraper for Marketing Junior jobs
- Create LinkedIn scraper for Marketing Junior jobs
- Implement filters for:
  - Experience level (entry/junior)
  - Marketing-related keywords
  - Vietnam locations
- Parse job details: title, company, salary, location
- Add company extraction and deduplication

### PR #3: Core API Endpoints (~200 lines)
- GET /api/jobs - List Marketing Junior jobs with filters
- GET /api/jobs/{id} - Get specific job details
- GET /api/companies - List companies hiring for Marketing
- GET /api/stats/marketing-junior - Marketing Junior statistics
- GET /api/filters/marketing-junior - Available filter options
- Implement pagination and sorting

### PR #4: React Frontend Setup (~150 lines)
- Initialize React app with TypeScript
- Configure API client for backend communication
- Create base layout for job listing platform
- Set up routing for jobs and companies
- Add Tailwind CSS for styling

### PR #5: Job Listing & Filtering UI (~250 lines)
- Create JobCard component optimized for Marketing positions
- Build filter sidebar for:
  - Experience level (entry/junior)
  - Location
  - Salary range
  - Job type
- Implement search for Marketing keywords
- Add responsive design for mobile

### PR #6: Company View & Statistics (~200 lines)
- Company listing page showing Marketing employers
- Marketing Junior statistics dashboard
- Salary trends visualization
- Top hiring companies for Marketing Juniors
- Location distribution chart

### PR #7: Automated Scraping & Scheduling (~150 lines)
- Set up APScheduler for daily scraping
- Configure scraping for Marketing Junior keywords:
  - "Marketing Junior"
  - "Marketing Fresh Graduate"
  - "Marketing Entry Level"
  - "Digital Marketing Junior"
- Implement job deduplication
- Add company data enrichment

### PR #8: Testing & Deployment (~150 lines)
- Add unit tests for scrapers
- Create integration tests for API endpoints
- Write frontend component tests
- Docker configuration for production
- Environment variables setup
- Deployment documentation

## Simplified Data Models

```python
# models/company.py
class Company:
    id: int
    name: str
    website: str  # optional
    industry: str  # focus on Marketing/Advertising
    created_at: datetime
    updated_at: datetime

# models/job.py
class Job:
    id: int
    external_id: str  # unique ID from source
    title: str
    company_id: int  # FK to Company
    description: str
    location: str
    url: str
    source: str  # 'indeed' or 'linkedin'
    job_type: str  # full-time/part-time/contract/internship
    experience_level: str  # entry/junior/mid/senior
    salary_min: decimal  # optional
    salary_max: decimal  # optional
    salary_currency: str  # VND
    posted_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

## API Endpoints (Aligned with API Contract)

```
# Jobs
GET  /api/jobs?experience_level=junior&search=marketing&page=1&limit=20
GET  /api/jobs/{id}
GET  /api/search/marketing-junior?location=ho-chi-minh&salary_min=8000000

# Companies  
GET  /api/companies?industry=marketing&page=1&limit=20

# Statistics
GET  /api/stats/marketing-junior

# Filters
GET  /api/filters/marketing-junior
```

## Frontend Routes

```
/                      - Marketing Junior job listings
/jobs/:id             - Job detail page
/companies            - Companies hiring for Marketing
/stats                - Marketing Junior statistics dashboard
```

## Key Features (Marketing Junior Focus)

1. **Targeted Scraping**: Focus on Marketing Junior/Entry positions
2. **Smart Filtering**: Pre-configured for junior-level Marketing roles
3. **Salary Insights**: Track salary ranges for Marketing Juniors
4. **Company Tracking**: Monitor companies actively hiring Marketing Juniors
5. **Daily Updates**: Automated scraping for fresh Marketing opportunities

## Scraping Strategy

### Keywords to Search
- Primary: "Marketing Junior", "Marketing Fresh Graduate"
- Secondary: "Digital Marketing Entry", "Marketing Intern"
- Location: "Vietnam", "Ho Chi Minh", "Hanoi"

### Data Extraction Priority
1. Jobs with "Junior" or "Entry" in title
2. Jobs with 0-2 years experience requirement
3. Marketing-related industries
4. Salary information when available

## Development Priorities

1. **MVP Focus**: Get Marketing Junior jobs displayed quickly
2. **Data Quality**: Ensure accurate experience level classification
3. **Performance**: Optimize queries for Marketing-specific filters
4. **User Experience**: Make it easy to find relevant Marketing Junior positions

## Success Metrics

- Number of Marketing Junior jobs scraped daily
- Accuracy of junior-level classification
- Companies actively hiring Marketing Juniors
- Average salary range for Marketing Junior positions
- Response time for filtered queries

## Future Enhancements (Post-MVP)

- Email alerts for new Marketing Junior positions
- Resume matching for Marketing skills
- Interview tips for Marketing Junior roles
- Salary negotiation guidance
- Career path visualization for Marketing professionals