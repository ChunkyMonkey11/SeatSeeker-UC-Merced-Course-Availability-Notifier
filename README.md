# SeatSeeker

SeatSeeker is a UC Merced course-availability notifier.

It provides:
- A Flask dashboard for subscription management
- A scheduler that checks CRNs and sends email notifications
- A shared SQLite/Postgres datastore
- Lightweight health and metrics endpoints
- A live queue scene that reflects people waiting for seat alerts

## Project Structure

- `main/app.py`: Flask app, API routes, DB initialization, metrics aggregation
- `main/checker_service.py`: Scheduler loop, availability checks, SMTP notifications
- `main/ClassChecker.py`: UC Merced registration scraper/checker
- `main/run.py`: CLI launcher (`dashboard`, `scheduler`, `scheduler-once`, `setup`, `status`)
- `main/templates/index.html`: Dashboard UI
- `main/config.env`: Environment template
- `main/wsgi.py`: WSGI entrypoint for Gunicorn
- `Dockerfile`: Container build for web service deployment
- `tests/`: Unit tests
- `docs/`: Architecture and operations docs

## Quick Start (Local)

```bash
cd main
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.env .env
python run.py setup
```

Start web dashboard:

```bash
python run.py dashboard
```

Start scheduler in a separate shell:

```bash
cd main
source venv/bin/activate
python run.py scheduler
```

Dashboard: `http://localhost:5000`

## Configuration

Edit `main/.env` (copied from `config.env`):

- `DATABASE_PATH`: SQLite path (default `database.db`)
- `DATABASE_URL`: Postgres connection URL (recommended for production/Supabase)
  - When set, `DATABASE_URL` takes precedence over `DATABASE_PATH`
- `EMAIL_SENDER`, `EMAIL_PASSWORD`, `SMTP_SERVER`, `SMTP_PORT`: SMTP settings
- `CHECK_INTERVAL`, `ERROR_RETRY_INTERVAL`: scheduler timings
- `TERM_CODE`: registration term code
- `SUBJECT_CODES`: comma-separated subjects; blank means all subjects
- `REQUEST_TIMEOUT_SECONDS`: HTTP timeout for checker requests
- `LOG_LEVEL`: scheduler log level
- `NOTIFY_MODE`: queue dispatch mode (`all` or `fifo`)
- `NOTIFY_BATCH_SIZE`: recipients per open CRN when `NOTIFY_MODE=fifo`
- `PRIORITY_EMAILS`: global priority emails (comma-separated)
- `PRIORITY_EMAILS_BY_CRN`: CRN-specific priority map (`12345:you@x.com|friend@x.com;23456:vip@x.com`)
- `PRIORITY_HOLD_MINUTES`: delay before notifying non-priority subscribers after priority recipients are notified
- `MAX_REQUEST_BODY_BYTES`: max request payload size for API requests
- `GLOBAL_RATE_LIMIT`: app-wide request limit
- `SUBSCRIPTION_POST_RATE`: rate limit for `POST /api/subscriptions`
- `SUBSCRIPTION_DELETE_RATE`: rate limit for `DELETE /api/subscriptions`
- `ADMIN_API_KEY`: required key for reading `GET /api/subscriptions` (header `X-SeatSeeker-Admin-Key`)
- `EXPOSE_INTERNAL_ERRORS`: set `true` only for debugging to expose DB error details in `/api/health`

Default term note:
- As of April 9, 2026, default `TERM_CODE` in project defaults is `202630`.

## API Endpoints

- `GET /`: Dashboard
- `GET /api/health`: Health status (`ok` or `degraded`)
- `GET /api/metrics`: Aggregated metrics (request totals, distinct profiles, status counts)
- `GET /api/subscriptions`: Subscriptions grouped by email (requires `X-SeatSeeker-Admin-Key`)
- `GET /api/sent-notifications`: Recent successful sends (requires `X-SeatSeeker-Admin-Key`)
- `POST /api/subscriptions`: Add subscriptions
- `DELETE /api/subscriptions`: Remove one subscription

## Testing

From repository root:

```bash
python3 -m pytest -q
```

## Deployment

### Option 1: Gunicorn (host process)

```bash
cd main
pip install -r requirements.txt
python run.py setup
gunicorn -c gunicorn.conf.py wsgi:app
```

Run scheduler as a second process:

```bash
python run.py scheduler
```

For persistent host deployments, prefer systemd units in `deploy/systemd/`.

Supabase note:
- Set `DATABASE_URL` in `main/.env` to your Supabase Postgres connection string.
- Run `python run.py setup` once to create tables/indexes.

### Option 2: Docker (web service)

```bash
docker build -t seatseeker .
docker run --rm -p 5000:5000 --env-file main/.env -v "$PWD/main:/app/main" seatseeker
```

For full functionality, run scheduler as a second process/container:

```bash
cd main
python run.py scheduler
```

## Monitoring

- Health check: `GET /api/health`
- Metrics: `GET /api/metrics`
- Scheduler logs: stdout/stderr
- Runtime status: `python run.py status`
