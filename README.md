# Smart Follow-Up Reminder

Smart Follow-Up Reminder is a local contact and conversation tracker for recruiters, clients, leads, and other professional relationships. It records who was contacted, what happened, and when the next action is due.

This first version is a personal-use local application. It has no authentication and is not yet a multi-user production service.

## Features

- Contact CRUD with validation and status tracking.
- Manage Contacts actions with confirmation-based deletion.
- Interaction history for email, calls, meetings, messages, and notes.
- Idempotent contact creation to prevent duplicate saves on retries or double-clicks.
- Dashboard counts for pending, replied, completed, due, overdue, and unscheduled contacts.
- Due-today, overdue, upcoming, and unscheduled follow-up views.
- SQLite persistence in `data/reminders.db`.
- FastAPI OpenAPI documentation at `/docs`.
- Streamlit UI communicating with FastAPI over HTTP.
- Temporary SQLite database tests, Ruff linting, and a Python 3.9-compatible setup.

## Architecture

The Streamlit frontend sends HTTP requests through `frontend/api_client.py`. FastAPI validates those requests with Pydantic, route modules call SQLAlchemy, and SQLAlchemy persists records in SQLite. The dashboard and follow-up endpoints query the same database, so refreshing Streamlit always reflects saved backend data.

```
Streamlit form -> frontend/api_client.py -> FastAPI /api/v1 -> Pydantic -> SQLAlchemy -> SQLite
                                                                    |
                                             dashboard/follow-up queries <-+
```

## Project Structure

```
backend/app/
  api/contacts.py       Contact CRUD
  api/interactions.py   Interaction history
  api/dashboard.py      Metrics and follow-up queries
  core/config.py        Environment settings
  database.py           Engine, sessions, table initialization
  models.py             Contact and Interaction ORM models
  schemas.py            Request and response validation
frontend/
  app.py                Streamlit pages
  api_client.py         HTTP-only frontend client
  components.py         Display helpers
.streamlit/config.toml  Light Streamlit theme and telemetry settings
backend/tests/          API tests using temporary SQLite files
data/                   Development database location
```

## Prerequisites

- Python 3.9 or newer. Python 3.11 is recommended.
- macOS/Linux shell or Windows PowerShell.

## Setup: macOS/Linux

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

## Setup: Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The VS Code interpreter is configured in `.vscode/settings.json`. Select `.venv/bin/python` on macOS/Linux or `.venv\\Scripts\\python.exe` on Windows if VS Code asks for an interpreter.

## Configuration

`.env.example` contains safe local defaults:

```env
DATABASE_URL=sqlite:///./data/reminders.db
BACKEND_URL=http://127.0.0.1:8000
APP_ENV=development
ENABLE_SCHEDULER=false
```

The `.env` file is ignored by Git. Do not put credentials in source code. The optional scheduler flag is reserved for a later notification stage; the mandatory in-app reminders work without email credentials.

The Streamlit theme is configured in `.streamlit/config.toml` with a warm off-white content area, dark-green sidebar, high-contrast header controls, and usage statistics disabled.

## Run the Application

The backend and frontend are separate processes. Open two terminals at the project root.

Terminal 1, macOS/Linux:

```bash
source .venv/bin/activate
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Terminal 1, Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

The backend is available at `http://127.0.0.1:8000`. Health check: `http://127.0.0.1:8000/health`. Interactive API documentation: `http://127.0.0.1:8000/docs`.

Terminal 2, macOS/Linux or Windows after activation:

```bash
.venv/bin/python -m streamlit run frontend/app.py
```

On Windows use:

```powershell
.venv\Scripts\python.exe -m streamlit run frontend/app.py
```

Streamlit normally opens at `http://localhost:8501`. Set `BACKEND_URL` before starting Streamlit if the API runs elsewhere.

A convenience backend launcher is also available:

```bash
.venv/bin/python run_app.py
```

## Database Initialization

Tables are created automatically when FastAPI starts. Existing rows are preserved; restarting the backend does not reset the database. The database file is ignored by Git. The `idempotency_records` table stores contact-submission keys and is created alongside the existing tables without resetting contacts. For tests, every test uses a separate temporary SQLite file.

## API Examples

Create a contact:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/contacts \
  -H 'Content-Type: application/json' \
  -d '{"name":"Rahul Sharma","company":"ABC Technologies","purpose":"Python backend opportunity","status":"Pending","next_follow_up_at":"2026-10-17T09:00:00Z"}'
```

For a retry-safe submission, send the same `Idempotency-Key` on each retry. The same key returns the original contact instead of creating another record:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/contacts \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: contact-form-submission-001' \
  -d '{"name":"Rahul Sharma","purpose":"Python backend opportunity"}'
```

Delete a contact and its interaction history:

```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/contacts/1
```

List pending contacts:

```bash
curl 'http://127.0.0.1:8000/api/v1/contacts?status=Pending&page=1&page_size=20'
```

Record an interaction:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/contacts/1/interactions \
  -H 'Content-Type: application/json' \
  -d '{"interaction_type":"Email","interaction_date":"2026-10-14T10:00:00Z","description":"Sent a follow-up email","outcome":"Waiting for reply"}'
```

## Follow-Up Rules

Incoming timestamps are normalized to UTC before storage. API responses include an explicit `Z` UTC suffix, while the Streamlit display converts them to the user's local timezone. Follow-ups are evaluated in UTC calendar boundaries to keep API behavior consistent across machines. Active statuses are `Pending`, `Replied`, and `No Response`. Completed contacts are excluded from due, overdue, and upcoming results.

- Due today: scheduled inside today's UTC date.
- Overdue: scheduled before today's UTC date.
- Upcoming: scheduled from tomorrow through the requested number of days.
- Unscheduled: no next follow-up timestamp.

An interaction updates `last_contacted_at` but does not automatically change the contact status or delete/reschedule its next follow-up.

## Tests and Quality Checks

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check backend frontend run_app.py
```

The suite covers health, validation, contact CRUD, interaction history, search, status filtering, pagination, UTC normalization, date boundaries, completed-contact exclusion, unscheduled follow-ups, idempotent creation, isolated deletion, and frontend API-client error handling. The current suite has 12 passing tests.

## Troubleshooting

- **Backend unavailable in Streamlit:** start FastAPI first and confirm `/health` returns `{"status":"ok"}`.
- **Port already in use:** start Uvicorn or Streamlit on another port and update `BACKEND_URL` as needed.
- **Duplicate contact after a retry:** keep the same `Idempotency-Key` for the entire form submission retry sequence.
- **Deleting from the UI:** open Manage Contacts, select Delete for the intended contact, review the contact-specific confirmation, then choose Delete permanently or Cancel deletion.
- **No follow-ups appear:** check the stored timezone-aware timestamp and confirm the contact status is not `Completed`.
- **Import error for `app`:** run Uvicorn from the project root with `--app-dir backend`.
- **Database permissions error:** ensure the project can write to `data/`.

## Known Limitations and Future Enhancements

Authentication, multi-user permissions, email delivery, notification history, and background scheduling are intentionally not enabled in this local first version. A future version can add Alembic migrations, PostgreSQL deployment, optional APScheduler email reminders with bounded retries, authentication, and timezone preferences per user.
