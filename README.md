# SFAO - Smart Feedback Analyzer for Organization

A unified offline intelligence platform designed to aggregate, analyze, and visualize organizational feedback using local NLP processing.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the backend:**
   ```bash
   python backend/main.py
   ```

3. **Access the app:**
   - Dashboard: http://localhost:8000/portal/dashboard
   - Survey: http://localhost:8000/portal/survey.html
   - Login is built into the dashboard
   - API Docs: http://localhost:8000/docs

4. **Generate test data:**
   ```bash
   python scripts/simulator.py
   ```
   This populates the database with mock feedback from social media sources (Twitter, Facebook, Instagram, LinkedIn, Reddit) and internal surveys.

## Architecture

- **Backend:** FastAPI + SQLite + VADER Sentiment Analysis
- **Frontend:** Modern HTML/CSS/JS with Chart.js
- **Database:** Offline SQLite vault (`sfao.db`)
- **AI:** Local sentiment analysis and categorization

## Features

- ✅ Real-time sentiment analysis
- ✅ Automated urgency flagging
- ✅ Multi-source feedback aggregation
- ✅ Executive dashboard with live charts
- ✅ Employee survey system
- ✅ Dashboard login overlay
- ✅ Action tracking (New → In-Progress → Resolved)
- ✅ Social media feedback ingestion (mock data via simulator)

## User Manual

### User Roles
- **Employees**: Submit feedback and track submissions.
- **Executives/Managers**: Monitor analytics and resolution progress.
- **Administrators**: Manage database and system operations.

### For Employees
1. **Access Dashboard**: Go to `http://localhost:8000/portal` and login with company email.
2. **Submit Feedback**: Navigate to Survey page, fill out the form with text, category, and rating.
3. **Track Progress**: View submission status in the dashboard (New → In-Progress → Resolved).

### For Executives
1. **Dashboard Access**: Visit `http://localhost:8000/portal/dashboard` for the HUD interface.
2. **Monitor Metrics**: View live charts for sentiment trends, categories, and urgency levels.
3. **Analyze Data**: Filter by time, category, or sentiment to identify patterns.

### For Administrators
1. **Database Studio**: Access `http://localhost:8001` for table views and management.
2. **Query Data**: Use `http://localhost:8001/query` for custom SQL queries.
3. **Analytics**: View advanced visualizations at `http://localhost:8001/analytics`.
4. **API Integration**: Refer to `http://localhost:8000/docs` for REST API endpoints.

### Key Workflows
- **Feedback Submission**: Employees submit → AI analyzes sentiment/urgency → Stored in database.
- **Resolution Tracking**: Executives assign actions → Update status → Monitor progress.
- **Reporting**: Generate insights from aggregated data for organizational improvements.

## Project Structure

```
SFAO/
├── backend/
│   ├── main.py      # FastAPI server
│   ├── brain.py     # NLP processing
│   ├── database.py  # SQLite operations
│   └── models/      # AI model storage
├── frontend/
│   ├── index.html   # Executive dashboard
│   └── survey.html  # Survey form
├── scripts/
│   └── simulator.py # Test data generator
├── sfao.db         # SQLite database
└── requirements.txt
```

## License

MIT License