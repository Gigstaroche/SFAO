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
   - Dashboard: http://localhost:8000/portal/index.html
   - Survey: http://localhost:8000/portal/survey.html
   - Portal: http://localhost:8000/portal/portal.html
   - API Docs: http://localhost:8000/docs

4. **Generate test data:**
   ```bash
   python scripts/simulator.py
   ```

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
- ✅ User authentication portal
- ✅ Action tracking (New → In-Progress → Resolved)

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
│   ├── survey.html  # Survey form
│   └── portal.html  # User portal
├── scripts/
│   └── simulator.py # Test data generator
├── sfao.db         # SQLite database
└── requirements.txt
```

## License

MIT License