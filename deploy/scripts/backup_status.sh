#!/usr/bin/env bash
set -Eeuo pipefail

# Print backup freshness and last restore drill timestamp.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${SEATSEEKER_BACKUP_DIR:-/var/backups/seatseeker}"
STATUS_FILE="${SEATSEEKER_BACKUP_STATUS_FILE:-$BACKUP_DIR/backup_status.env}"
FRESHNESS_MINUTES="${SEATSEEKER_BACKUP_FRESHNESS_MINUTES:-180}"

if [[ ! -f "$STATUS_FILE" ]]; then
  echo "status=missing"
  echo "message=No backup status file found at $STATUS_FILE"
  exit 1
fi

LAST_BACKUP_AT="$(grep '^LAST_BACKUP_AT=' "$STATUS_FILE" | cut -d'=' -f2- || true)"
LAST_BACKUP_FILE="$(grep '^LAST_BACKUP_FILE=' "$STATUS_FILE" | cut -d'=' -f2- || true)"
LAST_RESTORE_TEST_AT="$(grep '^LAST_RESTORE_TEST_AT=' "$STATUS_FILE" | cut -d'=' -f2- || true)"

if [[ -z "$LAST_BACKUP_AT" ]]; then
  echo "status=missing-backup-time"
  echo "message=LAST_BACKUP_AT not present in $STATUS_FILE"
  exit 1
fi

backup_epoch="$(date -u -d "$LAST_BACKUP_AT" +%s 2>/dev/null || true)"
if [[ -z "$backup_epoch" ]]; then
  backup_epoch="$(date -j -u -f '%Y-%m-%dT%H:%M:%SZ' "$LAST_BACKUP_AT" +%s 2>/dev/null || true)"
fi
if [[ -z "$backup_epoch" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    backup_epoch="$(python3 - <<PY
from datetime import datetime
try:
    print(int(datetime.strptime("$LAST_BACKUP_AT", "%Y-%m-%dT%H:%M:%SZ").timestamp()))
except ValueError:
    print("")
PY
)"
  fi
  if [[ -z "$backup_epoch" ]]; then
    echo "status=invalid"
    echo "message=Cannot parse LAST_BACKUP_AT=$LAST_BACKUP_AT"
    exit 1
  fi
fi

now_epoch="$(date -u +%s)"
age_minutes="$(( (now_epoch - backup_epoch) / 60 ))"

echo "status_file=$STATUS_FILE"
echo "last_backup_at=$LAST_BACKUP_AT"
echo "last_backup_file=${LAST_BACKUP_FILE:-unknown}"
echo "backup_age_minutes=$age_minutes"
echo "freshness_threshold_minutes=$FRESHNESS_MINUTES"
echo "last_restore_test_at=${LAST_RESTORE_TEST_AT:-never}"

if (( age_minutes > FRESHNESS_MINUTES )); then
  echo "status=stale"
  exit 1
fi

echo "status=fresh"
