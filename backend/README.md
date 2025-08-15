# Job Scraper Backend - PR #1: Backend Foundation

## Overview
Basic FastAPI backend setup with SQLite database connection and health check endpoints.

## Setup Instructions

1. **Create Python virtual environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
```

4. **Run the server:**
```bash
python run.py
# Or directly with uvicorn:
# uvicorn app.main:app --reload
```

## API Endpoints

- `GET /` - Welcome message and API info
- `GET /api/health` - Basic health check
- `GET /api/health/db` - Database connection health check
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app initialization
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py    # Settings configuration
│   ├── database/
│   │   ├── __init__.py
│   │   └── session.py   # Database session management
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py    # Health check endpoints
│   ├── models/          # (Empty - for next PR)
│   └── scrapers/        # (Empty - for future PRs)
├── run.py               # Application entry point
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore
└── README.md
```

## Testing

Test the health endpoints:
```bash
# Basic health check
curl http://localhost:8000/api/health

# Database health check
curl http://localhost:8000/api/health/db

# View API docs
open http://localhost:8000/docs
```

## Features Implemented
- ✅ FastAPI application setup
- ✅ SQLite database connection with SQLAlchemy
- ✅ Configuration management with Pydantic Settings
- ✅ CORS middleware for frontend integration
- ✅ Health check endpoints
- ✅ Auto-generated API documentation
- ✅ Environment-based configuration

## Total Lines of Code: ~150