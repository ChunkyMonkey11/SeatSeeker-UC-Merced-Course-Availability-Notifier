# Operations

## Runbook

### 1. Install

```bash
cd main
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.env .env
python run.py setup
```

### 2. Start Services

Web:

```bash
python run.py dashboard
```

Scheduler:

```bash
python run.py scheduler
```

One-shot scheduler check (useful for smoke checks):

```bash
python run.py scheduler-once
```

## Health and Metrics

- `GET /api/health`
  - Returns `200` for healthy DB connectivity
  - Returns `503` when degraded

- `GET /api/metrics`
  - `total_subscriptions`
  - `total_profiles`
  - `total_courses`
  - `status_counts`
  - `last_checked`

## Logging

- Scheduler logs to stdout with timestamps
- Set `LOG_LEVEL` in `.env` (e.g., `INFO`, `DEBUG`)

## Testing

From repo root:

```bash
python3 -m pytest -q
```

Current test coverage targets:
- Subscription API create/read/delete
- Metrics aggregation endpoint
- Scheduler behavior with mocked checker + mocked email sender

## Deployment

### Host (Gunicorn)

```bash
cd main
gunicorn -c gunicorn.conf.py wsgi:app
```

### Production Services (systemd)

Use the provided unit files:

- `deploy/systemd/seatseeker-dashboard.service`
- `deploy/systemd/seatseeker-scheduler.service`

Install and enable:

```bash
sudo cp deploy/systemd/seatseeker-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now seatseeker-dashboard
sudo systemctl enable --now seatseeker-scheduler
```

Operational commands:

```bash
sudo systemctl status seatseeker-dashboard --no-pager
sudo systemctl status seatseeker-scheduler --no-pager
sudo journalctl -u seatseeker-dashboard -f
sudo journalctl -u seatseeker-scheduler -f
```

### Docker (Web)

```bash
docker build -t seatseeker .
docker run --rm -p 5000:5000 --env-file main/.env -v "$PWD/main:/app/main" seatseeker
```

Run scheduler as a second process/container pointing at the same database file.

## Operational Notes

- Preferred production backend is Postgres via `DATABASE_URL` (for example Supabase).
- If using SQLite, maintain stable storage/volume.
- Ensure web and scheduler point to identical DB settings (`DATABASE_URL` or `DATABASE_PATH`).
- For Gmail, use app passwords rather than account password.
- Queue strategy controls notification fan-out:
  - `NOTIFY_MODE=all`: notify everyone waiting on an open CRN (default)
  - `NOTIFY_MODE=fifo`: notify first `NOTIFY_BATCH_SIZE` users per open CRN
- Priority strategy (optional):
  - `PRIORITY_EMAILS`: global emails always prioritized
  - `PRIORITY_EMAILS_BY_CRN`: CRN-scoped priority emails
  - `PRIORITY_HOLD_MINUTES`: wait window before notifying non-priority users
  - Hold state is persisted in table `priority_holds` so restarts do not reset timers
- `TERM_CODE` default has been updated to `202630` (Fall 2026) on 2026-04-09.
- Secret safety:
  - `.env` is ignored by git (`main/.gitignore`)
  - API returns sanitized error messages by default
  - Internal DB error details are hidden unless `EXPOSE_INTERNAL_ERRORS=true`

## Rate Limiting Defaults

- App-wide limit via Flask-Limiter:
  - `GLOBAL_RATE_LIMIT=120 per minute`
- Subscription mutation limits:
  - `SUBSCRIPTION_POST_RATE=10 per minute`
  - `SUBSCRIPTION_DELETE_RATE=20 per minute`
- Request body guardrail:
  - `MAX_REQUEST_BODY_BYTES=16384`

Tune these in `main/.env` for your traffic profile.

## Monitoring and Billing Guardrails

Create AWS alarms at minimum for:

- EC2 `StatusCheckFailed` >= 1
- EC2 CPUUtilization sustained high (for example >= 80% for 10 minutes)
- EC2 NetworkOut abnormal spikes

Create AWS Budgets alerts (email/SNS):

- Monthly budget cap: `$10`
- 50% (`$5`)
- 80% (`$8`)
- 100% (`$10`)
- 120% (`$12`) overrun alert

Also watch scheduler logs for repeated SMTP failures and notify on sustained error bursts.

## Email Worker Validation (Pre-Prod)

Automated test coverage includes SMTP send path in:

- `tests/test_checker_service.py` (`test_send_email_notification_uses_smtp_ssl_and_sends_message`)

Manual pre-prod smoke:

```bash
cd main
source venv/bin/activate
python3 run.py scheduler-once
```

Confirm:

- test inbox receives expected email when a known-open CRN is queued
- failures are logged and marked without crashing loop
