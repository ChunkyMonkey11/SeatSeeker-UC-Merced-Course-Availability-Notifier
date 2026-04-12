# Next Patch Plan: Sent Notification Audit History

## Goal
Preserve a durable history of successful notification sends so we can answer:
- Which email/CRN pairs were notified
- When notifications were sent
- How many alerts have been delivered over time

This addresses the current behavior where successful sends are removed from `subscriptions`, which makes historical reporting difficult.

## Scope (Next Patch)
1. Add a new table: `sent_notifications`.
2. Write an audit row for every successful email send.
3. Keep existing queue cleanup behavior (remove subscription after successful send) to avoid changing current user-facing flow.
4. Add read access for basic history reporting (SQL query + optional API endpoint).
5. Add tests covering audit writes and retrieval.
6. Update docs/runbook with new inspection commands.
7. Add an operator-only dashboard/log view on the SSH server, restricted to the maintainer IP, to visualize live queue/sent state.

## Proposed Schema
For SQLite:

```sql
CREATE TABLE IF NOT EXISTS sent_notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  crn TEXT NOT NULL,
  sent_at TEXT NOT NULL,
  term_code TEXT,
  source TEXT DEFAULT 'scheduler'
);
CREATE INDEX IF NOT EXISTS idx_sent_notifications_email ON sent_notifications(email);
CREATE INDEX IF NOT EXISTS idx_sent_notifications_crn ON sent_notifications(crn);
CREATE INDEX IF NOT EXISTS idx_sent_notifications_sent_at ON sent_notifications(sent_at);
```

For Postgres:

```sql
CREATE TABLE IF NOT EXISTS sent_notifications (
  id BIGSERIAL PRIMARY KEY,
  email TEXT NOT NULL,
  crn TEXT NOT NULL,
  sent_at TIMESTAMPTZ NOT NULL,
  term_code TEXT,
  source TEXT DEFAULT 'scheduler'
);
CREATE INDEX IF NOT EXISTS idx_sent_notifications_email ON sent_notifications(email);
CREATE INDEX IF NOT EXISTS idx_sent_notifications_crn ON sent_notifications(crn);
CREATE INDEX IF NOT EXISTS idx_sent_notifications_sent_at ON sent_notifications(sent_at);
```

## Implementation Notes
1. `main/db.py`
- Extend `init_db()` to create `sent_notifications` for both SQLite and Postgres.

2. `main/checker_service.py`
- On successful `send_email_notification(...)`, insert into `sent_notifications` before removing the live subscription row.
- Keep insertion and deletion in the same DB transaction block where possible.

3. `main/app.py` (optional, recommended)
- Add a protected admin endpoint (same admin key model) for recent sent history:
  - `GET /api/sent-notifications?limit=...`

4. Docs
- Add operator commands to `docs/IMPORTANT_COMMANDS.md` for:
  - total sent count
  - recent sent rows table view

5. Private ops visualization (SSH server)
- Add a lightweight operator dashboard route or static status page for:
  - current pending subscriptions
  - total sent notifications
  - recent sent notifications
  - optional per-CRN waiting counts
- Restrict access at network/proxy level to maintainer IP only (AWS Security Group and/or Nginx allowlist).
- Keep this separate from public user UI; no exposure of admin keys or sensitive data.

## Validation Plan
1. Unit/integration tests:
- Verify successful scheduler send creates one audit record.
- Verify failed send does not create audit record.
- Verify existing subscription delete-on-success behavior still works.

2. Manual checks:
- Run `python3 -m pytest -q`.
- Trigger one controlled successful notification path.
- Query:
  - `SELECT COUNT(*) FROM sent_notifications;`
  - `SELECT email, crn, sent_at FROM sent_notifications ORDER BY sent_at DESC LIMIT 20;`
- Verify private dashboard/log endpoint is reachable from maintainer IP and blocked from non-allowlisted IPs.

## Rollout / Safety
- Backward-compatible additive schema change only.
- No secret handling changes.
- Preserve rollback by keeping old behavior plus additive audit trail.
- Deploy with existing `deploy/scripts/safe_deploy.sh` flow (tests must pass before service restart).
- For private dashboard access, prefer IP allowlisting over app-level obscurity and verify deny behavior before announcing.

## Added Requirement: Backup + Failover Readiness
We need a backup strategy so data survives single-instance failure and can be restored on a replacement VM quickly.

### Objective
- Persist subscription and sent-notification data outside the current VM.
- Support fast recovery onto another instance with minimal data loss.

### Proposed Approach
1. Add scheduled backups of the operational database (`database.db`) to external durable storage.
2. Prefer external storage that is independent of the instance lifecycle (for example object storage or mounted network file system).
3. Document restore steps to bootstrap a replacement VM from latest backup.
4. Add a lightweight restore validation drill to confirm backups are actually usable.

### Minimum Deliverables
- Backup script (timestamped snapshots + retention policy).
- Scheduled execution (cron/systemd timer).
- Restore script and runbook docs.
- Operator command to verify backup freshness and last successful restore test date.

## Added Requirement: Private Visual Ops Dashboard + Endpoint
We need an operator-access view (private/admin-only) that shows:
1. Scrollable table of subscription rows (from `subscriptions`).
2. Sent total as an explicit numeric metric.

### Dashboard / Endpoint Expectations
- Add a dedicated private endpoint/page (for example `/admin/ops` and/or `/api/admin/ops-summary`).
- Render subscriptions in a visual table with scroll support (pagination or scroll container).
- Include a clearly labeled numeric field for total sent count:
  - Example key/label: `sent_total`
  - Value must be a number (integer), not text.
- Keep access restricted (admin key and/or IP allowlist).

### Data Requirements
- Subscription table data source: `subscriptions`.
- Sent count data source: `sent_notifications` count query.
- Include both:
  - total pending/waiting count
  - total sent count (numeric)

### Validation
- Verify dashboard loads only for authorized access.
- Verify unauthorized access is blocked.
- Verify subscription rows are scrollable and readable.
- Verify sent count is returned/rendered as a number and matches DB query result.
