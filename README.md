# AI Job Search

An intelligent job scraping application that helps Vietnamese Fresh Graduate Marketing professionals find relevant job opportunities from Indeed and LinkedIn.

## Features

- 🔍 Automated job scraping from Indeed and LinkedIn
- 🎯 Focused on Vietnamese market and Marketing positions
- 📊 Job filtering and search capabilities
- 🚀 Simple, clean architecture without overengineering
- 📱 Responsive web interface

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18 with TypeScript
- **Database**: SQLite
- **Scraping**: BeautifulSoup4 + Requests

## Project Structure

```
ai-job-search/
├── backend/          # FastAPI backend
│   └── app/         # Application code
├── frontend/        # React frontend (coming soon)
└── docs/           # Documentation
```

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Visit http://localhost:8000/docs for API documentation.

## Development Progress

- [x] PR #1: Backend Foundation
- [ ] PR #2: Database Models
- [ ] PR #3: Indeed Scraper
- [ ] PR #4: LinkedIn Scraper
- [ ] PR #5: API Endpoints
- [ ] PR #6: React Frontend Setup
- [ ] PR #7: Job Listing Components
- [ ] PR #8: Filters & Search
- [ ] PR #9: Background Scheduler
- [ ] PR #10: Docker Setup

## License

MIT