# Job Scraper Application - Implementation Plan

## Overview
A simple job scraping application targeting Vietnamese Fresher Marketing positions from Indeed and LinkedIn.

## Tech Stack
- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18 with TypeScript
- **Database**: MySQL 8.0 (more scalable than SQLite)
- **Scraping**: BeautifulSoup4 + Requests (keeping it simple)
- **Task Queue**: Simple cron-like scheduler with APScheduler
- **Deployment**: Docker Compose for MySQL and local development

## Architecture
```
job-scraper/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── scrapers/
│   │   ├── api/
│   │   └── database/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.tsx
│   └── package.json
└── docker-compose.yml
```

## Implementation Steps (Small PRs)

### PR #1: Backend Foundation (~150 lines)
- Set up FastAPI project structure
- Create basic configuration
- Set up MySQL database connection with Docker Compose
- Create health check endpoint
- Add requirements.txt with minimal dependencies

### PR #2: Database Models (~100 lines)
- Define Job model (SQLAlchemy)
- Create database tables
- Add migration script
- Implement basic CRUD operations

### PR #3: Indeed Scraper Module (~200 lines)
- Create Indeed scraper class
- Parse job listings (title, company, location, description)
- Handle pagination
- Add error handling and retry logic
- Focus on Vietnam market with Marketing keywords

### PR #4: LinkedIn Scraper Module (~200 lines)
- Create LinkedIn scraper class
- Handle LinkedIn's structure
- Parse job details
- Add rate limiting to be respectful
- Note: May need to use cookies/headers

### PR #5: API Endpoints (~150 lines)
- GET /api/jobs - List all jobs with pagination
- GET /api/jobs/{id} - Get specific job
- POST /api/scrape - Trigger manual scraping
- GET /api/stats - Get scraping statistics
- Add proper error handling

### PR #6: React Frontend Setup (~100 lines)
- Initialize React app with TypeScript
- Set up routing
- Create layout components
- Configure API client (axios)
- Add basic styling (Tailwind CSS)

### PR #7: Job Listing Components (~200 lines)
- Create JobCard component
- Create JobList component with pagination
- Add loading states
- Implement error boundaries
- Mobile responsive design

### PR #8: Job Details & Filters (~200 lines)
- Job detail view component
- Filter sidebar (company, location, date)
- Search bar component
- Sort options (date, relevance)
- Save/bookmark functionality

### PR #9: Background Scheduler (~150 lines)
- Set up APScheduler
- Create daily scraping tasks
- Add job deduplication logic
- Implement old job cleanup
- Add scraping status monitoring

### PR #10: Docker & Deployment (~100 lines)
- Create Dockerfile for backend
- Create Dockerfile for frontend
- Docker Compose configuration
- Environment variables setup
- Add README with setup instructions

## Data Model

```python
class Job:
    id: int
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str  # 'indeed' or 'linkedin'
    posted_date: datetime
    scraped_date: datetime
    salary: str  # optional
    job_type: str  # full-time, part-time, etc.
    is_active: bool
```

## API Endpoints

```
GET  /api/jobs?page=1&limit=20&search=marketing
GET  /api/jobs/{id}
POST /api/scrape/trigger
GET  /api/stats
GET  /api/companies
GET  /api/locations
```

## Frontend Routes

```
/           - Job listing page
/job/:id    - Job detail page
/stats      - Scraping statistics
/about      - About page
```

## Key Features (Keeping it Simple)

1. **Automated Daily Scraping**: Runs at 6 AM daily
2. **Search & Filter**: Basic text search and filters
3. **Duplicate Detection**: Based on URL and title
4. **Data Retention**: Keep jobs for 30 days
5. **Rate Limiting**: Respectful scraping with delays

## Important Considerations

1. **Robots.txt Compliance**: Check and respect robots.txt
2. **Rate Limiting**: Add delays between requests (2-5 seconds)
3. **User-Agent**: Use legitimate browser user-agent
4. **Error Handling**: Graceful failures, don't crash on errors
5. **Data Privacy**: Don't store personal information

## Development Workflow

1. Each PR should be tested independently
2. Include basic unit tests where applicable
3. Use environment variables for configuration
4. Add logging for debugging
5. Document API endpoints with FastAPI's auto-docs

## Future Enhancements (After MVP)

- Email notifications for new jobs
- User accounts and saved searches
- More job sources (VietnamWorks, TopCV)
- Advanced filtering (experience level, skills)
- Export to CSV/Excel
- Job application tracking