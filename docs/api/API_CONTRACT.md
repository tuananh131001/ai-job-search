# API Contract Documentation (Simplified)

## Base URL
```
Development: http://localhost:8000/api
Production: https://api.jobscraper.com/api
```

## Overview
Simplified API focused on fetching and filtering job listings, particularly for Marketing Junior positions.

## Common Response Format

### Success Response
```json
{
  "success": true,
  "data": {...},
  "message": "Operation successful"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {...}
  }
}
```

### Pagination Response
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total_items": 150,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## API Endpoints

### 1. Jobs

#### GET /api/jobs
Get paginated list of jobs with filtering options optimized for Marketing Junior positions.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | int | No | Page number (default: 1) |
| limit | int | No | Items per page (default: 20, max: 100) |
| search | string | No | Search in title and description (e.g., "Marketing") |
| location | string | No | Filter by location |
| company | string | No | Filter by company name |
| source | string | No | Filter by source (indeed/linkedin) |
| job_type | string | No | Filter by job type (full-time/part-time/contract/internship) |
| experience_level | string | No | Filter by experience level (entry/junior/mid/senior) |
| salary_min | number | No | Minimum salary filter |
| posted_after | date | No | Jobs posted after this date |
| sort_by | string | No | Sort field (posted_date/salary) |
| order | string | No | Sort order (asc/desc) |

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "external_id": "indeed_12345",
        "title": "Marketing Executive - Fresh Graduate",
        "company": {
          "id": 1,
          "name": "ABC Company",
          "industry": "Marketing & Advertising"
        },
        "location": "Ho Chi Minh City, Vietnam",
        "job_type": "full-time",
        "experience_level": "junior",
        "salary_range": {
          "min": 8000000,
          "max": 12000000,
          "currency": "VND"
        },
        "posted_date": "2024-01-15T10:00:00Z",
        "url": "https://indeed.com/...",
        "source": "indeed",
        "description_preview": "We are looking for a Marketing Junior...",
        "is_active": true
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total_items": 150,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

#### GET /api/jobs/{id}
Get detailed information about a specific job.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "external_id": "indeed_12345",
    "title": "Marketing Executive - Fresh Graduate",
    "company": {
      "id": 1,
      "name": "ABC Company",
      "website": "https://abc.com",
      "industry": "Marketing & Advertising"
    },
    "description": "Full job description for Marketing Junior position...",
    "location": "Ho Chi Minh City, Vietnam",
    "job_type": "full-time",
    "experience_level": "junior",
    "salary_range": {
      "min": 8000000,
      "max": 12000000,
      "currency": "VND"
    },
    "posted_date": "2024-01-15T10:00:00Z",
    "url": "https://indeed.com/...",
    "source": "indeed",
    "is_active": true,
    "created_at": "2024-01-15T12:00:00Z",
    "updated_at": "2024-01-15T12:00:00Z"
  }
}
```

### 2. Companies

#### GET /api/companies
Get list of companies hiring for Marketing positions.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | int | No | Page number (default: 1) |
| limit | int | No | Items per page (default: 20) |
| industry | string | No | Filter by industry (e.g., "Marketing") |
| search | string | No | Search in company name |

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "ABC Marketing Agency",
        "website": "https://abc.com",
        "industry": "Marketing & Advertising",
        "job_count": 5,
        "created_at": "2024-01-15T10:00:00Z"
      }
    ],
    "pagination": {...}
  }
}
```

### 3. Statistics

#### GET /api/stats/marketing-junior
Get statistics specifically for Marketing Junior positions.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_marketing_junior_jobs": 125,
    "active_marketing_junior_jobs": 89,
    "companies_hiring": 34,
    "average_salary": {
      "min": 8000000,
      "max": 15000000,
      "currency": "VND"
    },
    "jobs_by_location": {
      "Ho Chi Minh City": 60,
      "Hanoi": 40,
      "Da Nang": 25
    },
    "jobs_by_type": {
      "full-time": 80,
      "internship": 30,
      "contract": 15
    },
    "top_companies": [
      {
        "name": "ABC Marketing Agency",
        "job_count": 5,
        "industry": "Marketing & Advertising"
      }
    ]
  }
}
```

### 4. Search & Filters

#### GET /api/filters/marketing-junior
Get filter options specifically for Marketing Junior positions.

**Response:**
```json
{
  "success": true,
  "data": {
    "locations": [
      {"value": "ho-chi-minh", "label": "Ho Chi Minh City", "count": 60},
      {"value": "hanoi", "label": "Hanoi", "count": 40}
    ],
    "job_types": [
      {"value": "full-time", "label": "Full Time", "count": 80},
      {"value": "internship", "label": "Internship", "count": 30}
    ],
    "companies": [
      {"id": 1, "name": "ABC Marketing Agency", "industry": "Marketing", "count": 5}
    ],
    "salary_ranges": [
      {"label": "5-10M VND", "min": 5000000, "max": 10000000, "count": 45},
      {"label": "10-15M VND", "min": 10000000, "max": 15000000, "count": 35},
      {"label": "15-20M VND", "min": 15000000, "max": 20000000, "count": 10}
    ]
  }
}
```

#### GET /api/search/marketing-junior
Quick search endpoint for Marketing Junior positions.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| keywords | string | No | Additional keywords to search |
| location | string | No | Filter by location |
| salary_min | number | No | Minimum salary |
| company_id | int | No | Filter by specific company |
| page | int | No | Page number (default: 1) |
| limit | int | No | Items per page (default: 20) |

**Response:**
Same format as GET /api/jobs

## Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| RESOURCE_NOT_FOUND | 404 | Requested resource not found |
| VALIDATION_ERROR | 400 | Request validation failed |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Access denied |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

## Rate Limiting

- Anonymous users: 100 requests per hour
- Authenticated users: 1000 requests per hour
- Scraping endpoints: 10 requests per hour

Headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642338000
```

## Webhooks (Future)

### Job Alert Webhook
```json
{
  "event": "new_jobs",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "count": 5,
    "jobs": [...]
  }
}
```

## SDK Examples

### JavaScript/TypeScript
```typescript
import { JobScraperAPI } from '@jobscraper/sdk';

const api = new JobScraperAPI({
  baseURL: 'http://localhost:8000/api'
});

// Get Marketing Junior jobs
const marketingJobs = await api.jobs.list({
  search: 'Marketing',
  experience_level: 'junior',
  location: 'Vietnam',
  page: 1,
  limit: 20
});

// Get job details
const job = await api.jobs.get(123);

// Get companies hiring for Marketing
const companies = await api.companies.list({
  industry: 'Marketing',
  page: 1,
  limit: 20
});

// Get Marketing Junior statistics
const stats = await api.stats.getMarketingJunior();
```

### Python
```python
from jobscraper import JobScraperAPI

api = JobScraperAPI(
    base_url="http://localhost:8000/api"
)

# Get Marketing Junior jobs
marketing_jobs = api.jobs.list(
    search="Marketing",
    experience_level="junior",
    location="Vietnam",
    page=1,
    limit=20
)

# Get job details
job = api.jobs.get(123)

# Get companies hiring for Marketing
companies = api.companies.list(
    industry="Marketing",
    page=1,
    limit=20
)

# Get Marketing Junior statistics
stats = api.stats.get_marketing_junior()
```