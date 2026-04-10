# SeatSeeker Agent Rules

These rules are mandatory for any agent working in this repository.

## Core Rule

Always follow the production safety policy in:

- `docs/PRODUCTION_DEVELOPMENT_SAFETY.md`

If any request conflicts with that policy, pause and ask for explicit confirmation before proceeding.

## Non-Negotiable Requirements

1. Do not commit or deploy directly from exploratory work.
2. Keep production changes isolated and reviewable.
3. Require testing and staging validation before production changes.
4. Preserve rollback capability for every production release.
5. Never expose or commit secrets.

## Operational Defaults

1. Prefer feature branches over direct `main` work.
2. Prefer reproducible deploy commands/scripts over manual server changes.
3. Prefer small, reversible production changes.

## Admin Endpoint Note

`GET /api/subscriptions` is admin-only and requires:

- Header: `X-SeatSeeker-Admin-Key`
- Value: `ADMIN_API_KEY` from environment

Do not expose or log admin keys in chat, commits, or screenshots.
