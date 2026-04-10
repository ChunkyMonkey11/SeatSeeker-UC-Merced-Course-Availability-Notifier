# Steps to Production

This checklist is the minimum safe path to launch SeatSeeker and keep it stable.

## 1. Build a Reliable Intake Website

Goal: users can submit `email + CRNs` and reliably manage subscriptions.

- [ ] Keep web app running behind Gunicorn (`main/wsgi.py`), not Flask dev server.
- [ ] Ensure create/read/delete subscription API paths are working end-to-end.
- [ ] Verify uptime checks for `GET /api/health`.
- [ ] Use a production database (`DATABASE_URL`) instead of local-only SQLite when possible.
- [ ] Confirm scheduler and web app point to the same database.

## 2. Secure the Website (Input + App Security)

Goal: prevent common app-layer attacks (SQL injection, malformed input abuse, spam).

- [ ] Validate and sanitize input:
  - email format validation
  - CRN format validation (5-digit numeric)
  - trim whitespace and reject empty/invalid payloads
- [ ] Use parameterized DB queries only (no string-concatenated SQL).
- [ ] Add request size limits and reject oversized payloads.
- [ ] Add rate limiting on public endpoints (especially subscription POST/DELETE).
- [ ] Return generic errors in production (`EXPOSE_INTERNAL_ERRORS=false`).
- [ ] Keep secrets out of git (`.env` never committed).
- [ ] Add security headers via app or reverse proxy (at least baseline CSP/frame protections).

## 3. Protect EC2 from Abuse and Unexpected Billing

Goal: malicious traffic cannot run up cost or degrade service.

- [ ] Restrict inbound ports with Security Groups:
  - allow `80/443` publicly
  - restrict `22` (SSH) to your IP only
- [ ] Put Nginx or equivalent in front of Gunicorn and enforce IP request limits.
- [ ] Enable fail2ban (or equivalent) for repeated abusive requests/login attempts.
- [ ] Add AWS Budgets billing alerts (email/SNS) for monthly spend thresholds.
- [ ] Add CloudWatch alarms for unusual CPU/network spikes.
- [ ] Set SMTP sending guardrails:
  - per-cycle send caps
  - retry/backoff limits
  - log and alert on repeated send failures

## 4. Test the Email Worker Before Production

Goal: scheduler and email notification flow work safely before real users rely on it.

- [ ] Run one-shot scheduler test:
  - `cd main && python run.py scheduler-once`
- [ ] Validate SMTP credentials with a controlled test inbox.
- [ ] Verify both success and failure paths:
  - success sends and subscription cleanup
  - failure marks status/error without crashing loop
- [ ] Confirm scheduler logs are visible and timestamped.
- [ ] Confirm no duplicate-spam behavior during repeated checks.

## 5. Pre-Production Gate (Must Pass)

- [ ] `python3 -m pytest -q` passes.
- [ ] Manual smoke test passes:
  - health endpoint
  - add/remove one subscription
  - scheduler-once run
- [ ] Staging validation complete.
- [ ] Rollback version/tag prepared.

## 6. Launch and Monitor

- [ ] Deploy web process.
- [ ] Deploy scheduler process.
- [ ] Re-check `GET /api/health` and `GET /api/metrics`.
- [ ] Watch logs for first 24 hours.
- [ ] Verify billing and infrastructure alarms are active.

## 7. Ongoing Safety Rules

- [ ] Ship changes from feature branches only.
- [ ] Keep production and staging data/secrets separate.
- [ ] Rotate secrets if exposure is suspected.
- [ ] Keep this file, `docs/OPERATIONS.md`, and `docs/PRODUCTION_DEVELOPMENT_SAFETY.md` in sync.
