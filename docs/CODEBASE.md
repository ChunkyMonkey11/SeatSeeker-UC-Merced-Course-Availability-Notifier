# Codebase Guide

## Purpose

SeatSeeker monitors UC Merced registration data and notifies subscribers when requested CRNs become available.

## Directory Map

- `main/`
  - `app.py`: Flask app and HTTP API
  - `checker_service.py`: polling scheduler and notification flow
  - `ClassChecker.py`: external registration data fetch + filtering
  - `run.py`: command launcher
  - `wsgi.py`: Gunicorn entrypoint
  - `gunicorn.conf.py`: production web config
  - `templates/index.html`: UI
  - `config.env`: env template
  - `db.py`: DB backend abstraction (SQLite/Postgres)
  - `database.db`: SQLite database (local)
- `tests/`
  - `test_app_api.py`: API unit/integration tests
  - `test_checker_service.py`: scheduler behavior tests (mocked external calls)
- `docs/`
  - `ARCHITECTURE.md`
  - `OPERATIONS.md`

## Module Details

### `main/app.py`

Responsibilities:
- Initialize DB schema (`init_db`)
- Serve dashboard (`/`)
- Expose monitoring APIs (`/api/health`, `/api/metrics`)
- CRUD subscriptions (`/api/subscriptions`)

Important behaviors:
- Uses `DATABASE_URL` (Postgres) when present, otherwise `DATABASE_PATH` (SQLite)
- Enforces `(email, crn)` uniqueness via DB constraint
- Returns grouped subscriptions by email for UI rendering

### `main/checker_service.py`

Responsibilities:
- Run polling loop
- Compare open sections vs tracked CRNs
- Send email notifications

Important behaviors:
- Builds per-CRN queues so one open check can notify multiple subscribers efficiently
- Queue dispatch is configurable: `NOTIFY_MODE=all` or `NOTIFY_MODE=fifo`
- Supports priority-first notifications via `PRIORITY_EMAILS` and `PRIORITY_EMAILS_BY_CRN`
- Defers non-priority recipients using `priority_holds` for `PRIORITY_HOLD_MINUTES`
- If notification succeeds, subscription row is deleted
- If notification fails, row status is set to `error`
- Closed CRNs remain `pending` with refreshed `last_checked`

### `main/ClassChecker.py`

Responsibilities:
- Build UC Merced search URLs
- Fetch result payloads
- Extract open CRNs where seats are available

Configurable via env:
- `TERM_CODE` (default updated to `202630`)
- `SUBJECT_CODES`
- `REQUEST_TIMEOUT_SECONDS`

### `main/run.py`

Commands:
- `dashboard`
- `scheduler`
- `scheduler-once`
- `setup`
- `status`

## Data Contract

### Table: `subscriptions`

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | auto increment |
| email | TEXT | required |
| crn | TEXT | required |
| status | TEXT | defaults to `pending` |
| last_checked | TEXT | ISO timestamp |
| created_at | TIMESTAMP | default current timestamp |

Unique index behavior:
- Duplicate `(email, crn)` inserts are ignored.

## API Contract

### `GET /api/health`
Returns service + DB status and uptime.

### `GET /api/metrics`
Returns:
- subscription totals
- distinct profile totals
- distinct course totals
- status distribution
- latest `last_checked`

### `GET /api/subscriptions`
Returns subscription rows grouped by email.

### `POST /api/subscriptions`
Payload:
```json
{ "email": "student@example.com", "crns": ["12345", "54321"] }
```

### `DELETE /api/subscriptions`
Payload:
```json
{ "email": "student@example.com", "crn": "12345" }
```

## Testing Strategy

- `test_app_api.py`
  - DB-backed API route tests using temporary sqlite files
  - verifies create/read/delete + metrics aggregation
- `test_checker_service.py`
  - mocks `ClassChecker.run`
  - mocks `send_email_notification`
  - verifies deletion-on-success and error-marking-on-failure

## Deployment Notes

- Web service is containerized via `Dockerfile` and served by Gunicorn.
- Scheduler remains a separate process and should share the same DB storage.
- SMTP credentials must be set in `.env` before notifications can work.
