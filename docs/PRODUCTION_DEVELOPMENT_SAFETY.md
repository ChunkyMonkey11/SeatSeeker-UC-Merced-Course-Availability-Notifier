# Production Development Safety Policy

This policy defines how SeatSeeker is developed after initial production launch to minimize outages, bad deploys, and data risk.

## Branching and Promotion

1. `main` is production-only.
2. All changes must be developed on feature branches (`feature/*`, `fix/*`, or `chore/*`).
3. Changes are promoted through a staging validation step before production.

## Environments

1. Production and staging must use separate databases.
2. Staging must never point to production SMTP credentials or production-only secrets.
3. Any schema/data migration must be tested in staging before production.

## Testing and Verification

1. Run automated tests before deploy:
   - `python3 -m pytest -q`
2. Run one manual smoke check before deploy:
   - `GET /api/health` returns healthy
   - create + remove one test subscription
   - run `python run.py scheduler-once` without errors

## Deployment Safety

1. Use a repeatable deploy command/script (no ad-hoc manual edits on server).
2. Tag every production release (`vX.Y.Z`).
3. Keep rollback path ready:
   - previous release tag must be deployable immediately
   - rollback steps should be documented and tested periodically

## Secrets and Security

1. Never commit `.env` or credentials.
2. Rotate secrets immediately if exposure is suspected.
3. Keep default API error responses sanitized (do not expose internals in prod).

## Monitoring and Operations

1. Monitor:
   - `GET /api/health`
   - scheduler logs
2. Alert on scheduler stoppage or repeated email send failures.
3. Keep an operational runbook current in `docs/OPERATIONS.md`.

## Merge/Deploy Gate (Required)

A change is ready for production only if all items below are true:

- Feature branch used
- Staging validation complete
- Tests passed
- Smoke test passed
- Release tag prepared
- Rollback path confirmed
- Secrets posture reviewed
