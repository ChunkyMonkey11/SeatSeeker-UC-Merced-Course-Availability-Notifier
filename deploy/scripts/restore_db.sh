#!/usr/bin/env bash
set -Eeuo pipefail

# Restore a SeatSeeker SQLite backup archive.
# Supports local files, S3 URIs, and "latest" from local backup dir.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_DIR="$REPO_DIR/main"

DB_PATH="${SEATSEEKER_DB_PATH:-$APP_DIR/database.db}"
BACKUP_DIR="${SEATSEEKER_BACKUP_DIR:-/var/backups/seatseeker}"
STATUS_FILE="${SEATSEEKER_BACKUP_STATUS_FILE:-$BACKUP_DIR/backup_status.env}"

BACKUP_INPUT=""
TARGET_DB_PATH="$DB_PATH"
DRILL_MODE="false"

usage() {
  cat <<'EOF'
Usage:
  restore_db.sh --backup <archive-path|s3://...|latest> [--target-db <path>] [--drill]

Options:
  --backup     Required backup source.
  --target-db  Destination database path (default: SEATSEEKER_DB_PATH or main/database.db).
  --drill      Validate restore on a temporary DB without replacing live DB.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup)
      BACKUP_INPUT="${2:-}"
      shift 2
      ;;
    --target-db)
      TARGET_DB_PATH="${2:-}"
      shift 2
      ;;
    --drill)
      DRILL_MODE="true"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$BACKUP_INPUT" ]]; then
  echo "ERROR: --backup is required"
  usage
  exit 1
fi

if [[ "$BACKUP_INPUT" == "latest" ]]; then
  latest_file="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'database-*.tar.gz' | sort | tail -n 1)"
  if [[ -z "$latest_file" ]]; then
    echo "ERROR: no local backup archive found in $BACKUP_DIR"
    exit 1
  fi
  BACKUP_INPUT="$latest_file"
fi

TMP_DIR="$(mktemp -d)"
WORK_ARCHIVE="$TMP_DIR/backup.tar.gz"
EXTRACT_DIR="$TMP_DIR/extracted"
mkdir -p "$EXTRACT_DIR"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

if [[ "$BACKUP_INPUT" == s3://* ]]; then
  if ! command -v aws >/dev/null 2>&1; then
    echo "ERROR: aws CLI required for S3 restore source"
    exit 1
  fi
  echo "Downloading backup archive from $BACKUP_INPUT"
  aws s3 cp "$BACKUP_INPUT" "$WORK_ARCHIVE"
else
  if [[ ! -f "$BACKUP_INPUT" ]]; then
    echo "ERROR: backup archive not found: $BACKUP_INPUT"
    exit 1
  fi
  cp "$BACKUP_INPUT" "$WORK_ARCHIVE"
fi

tar -xzf "$WORK_ARCHIVE" -C "$EXTRACT_DIR"
RESTORED_DB="$EXTRACT_DIR/database.db"
if [[ ! -f "$RESTORED_DB" ]]; then
  echo "ERROR: backup archive does not contain database.db"
  exit 1
fi

if command -v sqlite3 >/dev/null 2>&1; then
  integrity="$(sqlite3 "$RESTORED_DB" "PRAGMA integrity_check;" | tr -d '[:space:]')"
  if [[ "$integrity" != "ok" ]]; then
    echo "ERROR: restored backup integrity check failed: $integrity"
    exit 1
  fi
fi

TIMESTAMP_FILE="$(date -u +'%Y-%m-%dT%H-%M-%SZ')"
TIMESTAMP_ISO="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

if [[ "$DRILL_MODE" == "true" ]]; then
  drill_target="$TMP_DIR/restore-drill.db"
  cp "$RESTORED_DB" "$drill_target"
  if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$drill_target" "SELECT COUNT(*) AS subscriptions FROM subscriptions;" >/dev/null
    has_sent_notifications="$(sqlite3 "$drill_target" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='sent_notifications';")"
    if [[ "$has_sent_notifications" == "1" ]]; then
      sqlite3 "$drill_target" "SELECT COUNT(*) AS sent FROM sent_notifications;" >/dev/null
    fi
  fi
  echo "Restore drill succeeded using backup: $BACKUP_INPUT"
else
  mkdir -p "$(dirname "$TARGET_DB_PATH")"
  if [[ -f "$TARGET_DB_PATH" ]]; then
    rollback_copy="${TARGET_DB_PATH}.pre_restore.${TIMESTAMP_FILE}.bak"
    cp "$TARGET_DB_PATH" "$rollback_copy"
    echo "Rollback copy created: $rollback_copy"
  fi
  cp "$RESTORED_DB" "$TARGET_DB_PATH"

  if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$TARGET_DB_PATH" "PRAGMA integrity_check;" | grep -qx "ok"
  fi

  echo "Restore completed to $TARGET_DB_PATH from $BACKUP_INPUT"
fi

last_backup_at="unknown"
last_backup_file="unknown"
last_backup_sha256="unknown"
last_backup_size="unknown"

if [[ -f "$STATUS_FILE" ]]; then
  last_backup_at="$(grep '^LAST_BACKUP_AT=' "$STATUS_FILE" | cut -d'=' -f2- || true)"
  last_backup_file="$(grep '^LAST_BACKUP_FILE=' "$STATUS_FILE" | cut -d'=' -f2- || true)"
  last_backup_sha256="$(grep '^LAST_BACKUP_SHA256=' "$STATUS_FILE" | cut -d'=' -f2- || true)"
  last_backup_size="$(grep '^LAST_BACKUP_SIZE_BYTES=' "$STATUS_FILE" | cut -d'=' -f2- || true)"
fi

cat > "$STATUS_FILE" <<EOF
LAST_BACKUP_AT=${last_backup_at:-unknown}
LAST_BACKUP_FILE=${last_backup_file:-unknown}
LAST_BACKUP_SHA256=${last_backup_sha256:-unknown}
LAST_BACKUP_SIZE_BYTES=${last_backup_size:-unknown}
LAST_RESTORE_TEST_AT=$TIMESTAMP_ISO
EOF

echo "Updated restore test timestamp in $STATUS_FILE"
