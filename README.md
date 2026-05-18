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

## System Monitoring (Admin)

- Live audit logs capturing monitoring events: frontend crashes, unhandled rejections, performance samples, click events and synthetic health pings.
- Roles and access:
  - `admin`: can capture telemetry from the app and view monitoring logs for regular users.
  - `super_admin`: can capture telemetry and view monitoring logs for admin-level actions.
  - `dev_admin`: view-only auditor — can see all monitoring logs and export them as CSV but cannot ingest events or use other admin functionality.
  - Regular users (`employee`, `analyst`, etc.): do NOT capture telemetry and cannot view monitoring UI.
- Endpoints:
  - `POST /admin/monitoring/events` — ingest monitoring events (requires `monitoring:ingest` permission).
  - `GET  /admin/monitoring/overview` — returns summary and recent events (requires `monitoring:view`).
  - `GET  /admin/audit` — generic audit listing (requires `monitoring:view`).
- Frontend behavior:
  - Monitoring telemetry is only active for `admin` and `super_admin` users (and the panel is visible to `dev_admin` for viewing/export only).
  - Admin and dev users can refresh the monitoring panel with the `Refresh` button and export logs with the `Export` button.

## Monitoring Export

- The dashboard provides CSV export for monitoring logs. Use the `Export` button in the System Monitoring header. The CSV includes: `id,event_type,actor_user_id,user_email,user_role,page,target_type,target_id,details,created_at`.

## Presentation Notes (slides / demo checklist)

1. Intro (1 slide): Overview of SFAO goals — capture feedback, analyze sentiment, route to teams.
2. Architecture (1 slide): Frontend (HTML/Chart.js), Backend (FastAPI + SQLite), Local NLP.
3. Live Demo Plan (3–5 minutes):
   - Show Dashboard landing (login as `employee`) — submit a quick feedback.
   - Login as `admin` (admin@sfao.local) — show live charts, then open System Monitoring panel and demonstrate telemetry capture.
   - Login as `dev_admin` (dev@sfao.local) — show monitoring-only view and export CSV.
4. Monitoring Details (1 slide): explain role model, what is captured (crashes, performance, synthetic pings), privacy considerations (no survey/answer data logged by default), and export capability.
5. Operational Runbook (1 slide): how to seed users, restart services, where logs are stored (`sfao.db`) and how to query them in `backend/database.py`.
6. Q&A / Next steps: integrating external APMs, retention policy, anonymization options.

## Running & Testing

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the services (recommended):
   ```bash
   python start_sfao.py
   ```

   This launches the main API on port 8000 and the Database Studio on port 8001.

3. Seed test users (creates `admin`, `dev_admin`, `employee`, `analyst`):
   ```bash
   python backend/seed_users.py
   ```

4. Test accounts (local):
   - Admin:  admin@sfao.local / AdminPass123!
   - Dev:    dev@sfao.local   / DevPass123!
   - Employee: employee@sfao.local / EmployeePass123!

5. Visit the app:
   - Dashboard / Portal: http://localhost:8000/portal
   - API docs: http://localhost:8000/docs
   - Database Studio: http://localhost:8001

6. Monitoring smoke test (admin):
   ```bash
   curl -X POST http://localhost:8000/admin/monitoring/events \
     -H "Authorization: Bearer <ADMIN_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"event_type":"error","details":{"message":"test error","user_role":"admin"}}'
   ```

## Notes & Troubleshooting

- If the System Monitoring panel is blank for `dev_admin`, refresh the page and ensure you are logged in as `dev@sfao.local`.
- If export fails, open browser DevTools Console to inspect errors and network requests to `/admin/monitoring/overview`.
- To change role permissions, update `ROLE_PERMISSIONS` in `backend/main.py` and restart the API.

## Contact / Maintainers

- For development questions, contact the SFAO maintainers listed in the project metadata.
