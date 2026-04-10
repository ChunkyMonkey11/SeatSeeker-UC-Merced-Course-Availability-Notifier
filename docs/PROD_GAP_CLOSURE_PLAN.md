# Production Gap Closure Plan

This plan closes the four blockers identified before launch:

1. rate limiting
2. process manager resilience
3. monitoring + billing alerts
4. email worker validation in deployed environment

## 1) Rate Limiting and Request Guardrails

Status: `implemented in code`, `needs deploy validation`

- Added Flask-Limiter controls in `main/app.py`
  - global request cap
  - strict limits on subscription mutation endpoints
- Added request body limit (`MAX_REQUEST_BODY_BYTES`)
- Added config knobs in `main/config.env`
- Added test coverage in `tests/test_app_api.py`

Deploy validation:

1. Submit two rapid `POST /api/subscriptions` requests from same client IP.
2. Confirm second request returns HTTP `429`.

## 2) Process Manager and Auto-Restart

Status: `unit files prepared`, `needs host install`

- Added systemd units:
  - `deploy/systemd/seatseeker-dashboard.service`
  - `deploy/systemd/seatseeker-scheduler.service`

Deploy validation:

1. Install + enable both services.
2. Confirm status is `active (running)`.
3. Reboot instance and verify both services auto-start.

## 3) Monitoring and Billing Alerts

Status: `runbook documented`, `needs AWS setup`

Required AWS actions:

1. CloudWatch alarms:
   - EC2 `StatusCheckFailed >= 1`
   - High CPU sustained
   - NetworkOut anomaly/spike
2. AWS Budgets alerts:
   - Monthly budget cap: `$10`
   - Alert thresholds:
     - 50% (`$5`)
     - 80% (`$8`)
     - 100% (`$10`)
     - 120% (`$12`) overrun alert
3. Add recipient email/SNS and verify alert delivery.

## 4) Email Worker Validation

Status: `automated SMTP test added`, `manual deployed smoke pending`

Automated test:

- `tests/test_checker_service.py`
  - `test_send_email_notification_uses_smtp_ssl_and_sends_message`

Deployed smoke test:

1. Add one controlled test subscription for a known-open CRN.
2. Run `python3 run.py scheduler-once`.
3. Confirm test inbox receives notification.
4. Confirm failure path marks row `error` without killing scheduler loop.

## Go-Live Gate

Production can be called ready when all are true:

- [ ] Rate-limit deploy validation passes (`429` observed correctly)
- [ ] systemd services running and restart-proof
- [ ] CloudWatch + Budget alerts configured and tested
- [ ] Email worker smoke test passes in deployed environment
