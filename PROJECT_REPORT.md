# SFAO — Project Report

## Title
Smart Feedback Analyzer for Organization (SFAO)

## Abstract
SFAO is a unified offline intelligence platform that aggregates, analyzes, and visualizes organizational feedback using local NLP processing. It supports multi-source ingestion (surveys and social mock data), local sentiment analysis, urgency flagging, and an executive dashboard with action tracking.

## Table of Contents
- Abstract
- Project Overview
- Architecture (diagram)
- Database & Models
- Backend Components
- Frontend Overview
- Portal Phase Plan
- How to Run
- Screenshots & Diagrams
- Impact & Use Cases
- Appendix (key snippets)

---

## Project Overview
SFAO provides:
- Real-time sentiment analysis and urgency flagging
- Aggregation of feedback from multiple sources
- Dashboard for executives, monitoring and query interface
- Database Studio (Prisma-like) for visualization and SQL queries

Key features and tech stack:
- Backend: FastAPI, SQLAlchemy, Alembic
- Frontend: Static HTML/CSS/JS (Chart.js for visualizations)
- Database: SQLite (`sfao.db`) — offline vault
- NLP: VADER sentiment analysis (local)

---

## Architecture
```mermaid
flowchart LR
  A[Sources: Surveys, Social Mock Data] --> B[Ingest API (/ingest, /survey)]
  B --> C[Analysis: brain.py]
  C --> D[Database: SQLite (sfao.db)]
  D --> E[API & Dashboard: FastAPI /portal]
  D --> F[Database Studio: / (port 8001)]
  E --> G[Frontend: Charts, Dashboards, Survey UI]
```

---

## Database & Models
Prisma schema (summary):

```
model Feedback { id Int @id @default(autoincrement()) source String text String sentiment String score Float category String urgency String status String created_at DateTime }

model User { id Int @id @default(autoincrement()) name String email String @unique password String role String created_at DateTime }
```

SQLAlchemy models and migration support are implemented (see `backend/models.py` and Alembic folder).

---

## Backend Components
- `backend/main.py`: FastAPI app with routes for `/ingest`, `/survey`, `/feed`, user management, monitoring, and static frontend mounting.
- `backend/brain.py`: NLP pipeline using VADER (clean_text, get_sentiment, get_category, get_urgency, analyze).
- `backend/database.py`: SQLite helper functions (init_db, insert_feedback, get_summary, user management).
- `backend/models.py` & `backend/schemas.py`: SQLAlchemy models and Pydantic schemas for validation.

A key analysis function (excerpt):

```python
# from backend/brain.py
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()

def analyze(text: str, source: str = "Unknown") -> dict:
    cleaned = clean_text(text)
    sentiment, score = get_sentiment(cleaned)
    category = get_category(cleaned)
    urgency = get_urgency(cleaned)
    return {"sentiment": sentiment, "score": score, "category": category, "urgency": urgency}
```

---

## Frontend Overview
Static HTML files live in `frontend/` including `index.html`, `survey.html`, and admin-like pages such as `manage-users.html`. Charts use Chart.js and pages are mounted under `/portal` by the FastAPI app.

---

## Portal Phase Plan (Summary)
Phased rollout from access foundation to buyer-specific tailoring (Safaricom). Key phases: Access Foundation, Operations Core & DB Expansion, Social Monitoring UI, Survey Builder, Resolver Workflow, Buyer Tailoring.

---

## How to Run
1. Create and activate a Python venv

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Seed users (optional):

```bash
python backend/seed_users.py
```

3. Start services (recommended):

```bash
python start_sfao.py
```

- API: http://localhost:8000
- Portal dashboard: http://localhost:8000/portal/dashboard
- Database Studio: http://localhost:8001

---

## Screenshots & Diagrams
Include images (screenshots, architecture diagrams, sample charts) in the `assets/` folder and re-run conversion. Placeholder images can be added under `frontend/assets/` or `assets/`.

Suggested images to include:
- Dashboard landing screenshot
- Sample sentiment chart (doughnut)
- Database Studio table view screenshot
- Architecture diagram (SVG/PNG)

---

## Impact & Use Cases
- Centralized feedback analysis for operations and product teams
- Faster identification of critical incidents via urgency flags
- Role-based dashboards for executives and operators
- Offline-first design suitable for environments with limited connectivity

---

## Appendix — Key Files Referenced
- `README.md`
- `DATABASE_INTEGRATION.md`
- `PORTAL_PHASE_PLAN.md`
- `prisma/schema.prisma`
- `backend/brain.py`
- `backend/database.py`
- `backend/main.py`

---

End of report.
