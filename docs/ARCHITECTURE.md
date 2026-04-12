# Architecture

## Goal

SeatSeeker tracks user-requested CRNs and notifies subscribers by email when seats open.

## Runtime Model

Two processes share one database (SQLite for local dev, Postgres recommended for production):

1. Web process (`main/app.py`)
- Serves dashboard UI
- Exposes subscription + monitoring APIs
- Aggregates metrics used by the UI

2. Scheduler process (`main/checker_service.py`)
- Polls UC Merced registration APIs
- Compares open CRNs against subscriptions
- Sends SMTP notifications
- Removes successfully notified subscriptions

## Components

- `main/ClassChecker.py`
  - Builds term/subject query URLs
  - Fetches registration data
  - Produces set of open CRNs

- `main/app.py`
  - Initializes DB schema
  - CRUD operations for subscriptions
  - Monitoring routes: `/api/health`, `/api/metrics`
  - Admin routes: `/api/subscriptions`, `/api/sent-notifications`, `/api/admin/ops-summary`, `/admin/ops`

- `main/checker_service.py`
  - Scheduler loop (`main()`)
  - One-pass check (`check_availability()`)
  - Email dispatch (`send_email_notification()`)

- `main/run.py`
  - Operational CLI wrapper

- `main/templates/index.html`
  - Dashboard
  - Live queue scene fed by `/api/metrics`

## Data Model

Table: `subscriptions`

- `id` (PK)
- `email` (TEXT, required)
- `crn` (TEXT, required)
- `status` (`pending`/`error`/`available`-style state)
- `last_checked` (ISO timestamp text)
- `created_at` (timestamp)
- unique constraint: `(email, crn)`

Table: `sent_notifications`

- `id` (PK)
- `email` (TEXT, required)
- `crn` (TEXT, required)
- `sent_at` (timestamp)
- `term_code` (TEXT)
- `source` (TEXT, default `scheduler`)

## Request/Notification Flow

1. User submits email + CRNs via dashboard.
2. API inserts unique subscriptions.
3. Scheduler fetches UC Merced registration JSON for `TERM_CODE` (current default: `202630`).
4. Scheduler groups subscriptions into per-CRN queues.
5. For each CRN queue:
   - If closed: keep subscriptions as `pending` and update `last_checked`.
   - If open:
     - split queue into `priority` and `non-priority` recipients (`PRIORITY_EMAILS`, `PRIORITY_EMAILS_BY_CRN`)
     - notify priority recipients first
     - if any priority notification is sent and non-priority users exist, create a hold window in `priority_holds` for `PRIORITY_HOLD_MINUTES`
     - during active hold, non-priority users stay pending
     - after hold expires, notify the non-priority queue
     - successful sends write `sent_notifications` audit rows and delete subscription rows
     - failures mark row status `error`

## Deployment Shape

- Web: Gunicorn + `main/wsgi.py`
- Scheduler: standalone Python process (`python run.py scheduler`)
- For SQLite: shared volume/storage required when containerized
- For Postgres (Supabase): both services share one `DATABASE_URL`

## Input -> Processing -> Polling (Concise)

1. Input: `email` + list of 5-digit `crn` values via `POST /api/subscriptions`.
2. Processing: API validates/sanitizes data, deduplicates CRNs, and stores queue rows in `subscriptions`.
3. Polling system: `main/checker_service.py` loop calls `ClassChecker.run()` every `CHECK_INTERVAL`.
4. Polling data source: UC Merced registration endpoints in `main/ClassChecker.py`.
5. Action: scheduler maps open CRNs to queued subscribers and sends SMTP notifications.
