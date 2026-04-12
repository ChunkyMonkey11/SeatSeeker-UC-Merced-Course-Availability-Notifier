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

- `GET /api/sent-notifications` (admin-only, requires `X-SeatSeeker-Admin-Key`)
  - Recent successful notification audit rows
  - Fields include `email`, `crn`, `sent_at`, `term_code`, `source`

- `GET /api/admin/ops-summary` (admin-only, requires `X-SeatSeeker-Admin-Key`)
  - `sent_total` (integer)
  - `waiting_total`
  - `pending_total`
  - `subscriptions`
  - `recent_sent_notifications`
  - `per_crn_waiting_counts`

- `GET /admin/ops` (admin-only, requires `X-SeatSeeker-Admin-Key`)
  - Private visual dashboard with scrollable subscriptions table and sent metrics

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
- Sent notification audit writes + retrieval
- Private ops summary/dashboard authorization

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
- Successful sends are persisted in `sent_notifications` before queue-row deletion.
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

## Private Ops Access Model

- Admin routes are protected by header:
  - `X-SeatSeeker-Admin-Key: <ADMIN_API_KEY>`
- Optional app-level IP allowlist:
  - `ADMIN_ALLOWLIST_IPS=203.0.113.10,198.51.100.22`
- Network-level restriction is still required in production:
  - AWS Security Group ingress: allow maintainer IP only for admin-exposed port/path
  - Nginx allowlist for `/admin/ops` and `/api/admin/*` paths

## Database Backup and Recovery

### Backup scripts

- `deploy/scripts/backup_db.sh`
  - Creates timestamped `database-<UTC>.tar.gz` snapshots
  - Keeps local retention (`SEATSEEKER_BACKUP_RETENTION`)
  - Optionally uploads to S3 (`SEATSEEKER_BACKUP_S3_URI`)
  - Writes backup metadata to `backup_status.env`

- `deploy/scripts/restore_db.sh`
  - Restores from local archive, S3 archive, or `--backup latest`
  - Creates a rollback copy before non-drill restore
  - `--drill` validates restore without replacing production DB

- `deploy/scripts/backup_status.sh`
  - Reports backup freshness
  - Reports `LAST_RESTORE_TEST_AT`
  - Exits non-zero when backup age exceeds `SEATSEEKER_BACKUP_FRESHNESS_MINUTES`

### Timer units

- `deploy/systemd/seatseeker-db-backup.service`
- `deploy/systemd/seatseeker-db-backup.timer` (every 30 minutes)
- `deploy/systemd/seatseeker-db-restore-drill.service`
- `deploy/systemd/seatseeker-db-restore-drill.timer` (weekly)

Install and enable on EC2:

```bash
sudo cp deploy/systemd/seatseeker-db-backup.service /etc/systemd/system/
sudo cp deploy/systemd/seatseeker-db-backup.timer /etc/systemd/system/
sudo cp deploy/systemd/seatseeker-db-restore-drill.service /etc/systemd/system/
sudo cp deploy/systemd/seatseeker-db-restore-drill.timer /etc/systemd/system/
sudo cp deploy/systemd/seatseeker-backup.env.example /etc/default/seatseeker-backup
sudoedit /etc/default/seatseeker-backup
sudo systemctl daemon-reload
sudo systemctl enable --now seatseeker-db-backup.timer
sudo systemctl enable --now seatseeker-db-restore-drill.timer
```

### Restore a replacement VM quickly

1. Provision VM and clone repo.
2. Install Python env and dependencies.
3. Copy `/etc/default/seatseeker-backup` (or recreate from secure secret store).
4. Pull latest backup archive from S3 or local durable volume.
5. Run restore:
   - `sudo ./deploy/scripts/restore_db.sh --backup <archive-or-s3-uri>`
6. Run smoke checks:
   - `curl -sS http://127.0.0.1:5000/api/health`
   - `python3 main/run.py scheduler-once`
7. Re-enable services after validation.

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
