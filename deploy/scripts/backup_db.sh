#!/usr/bin/env bash
set -Eeuo pipefail

# Create timestamped SQLite backups with retention and optional S3 upload.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_DIR="$REPO_DIR/main"

DB_PATH="${SEATSEEKER_DB_PATH:-$APP_DIR/database.db}"
BACKUP_DIR="${SEATSEEKER_BACKUP_DIR:-/var/backups/seatseeker}"
RETENTION_COUNT="${SEATSEEKER_BACKUP_RETENTION:-14}"
REMOTE_RETENTION_COUNT="${SEATSEEKER_BACKUP_REMOTE_RETENTION:-30}"
S3_URI="${SEATSEEKER_BACKUP_S3_URI:-}"
STATUS_FILE="${SEATSEEKER_BACKUP_STATUS_FILE:-$BACKUP_DIR/backup_status.env}"

mkdir -p "$BACKUP_DIR"

if [[ ! -f "$DB_PATH" ]]; then
  echo "ERROR: database file not found at $DB_PATH"
  exit 1
fi

TIMESTAMP_FILE="$(date -u +'%Y-%m-%dT%H-%M-%SZ')"
TIMESTAMP_ISO="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
ARCHIVE_NAME="database-${TIMESTAMP_FILE}.tar.gz"
ARCHIVE_PATH="$BACKUP_DIR/$ARCHIVE_NAME"
STAGING_DIR="$(mktemp -d "$BACKUP_DIR/staging.XXXXXX")"
SNAPSHOT_DB="$STAGING_DIR/database.db"
MANIFEST_FILE="$STAGING_DIR/manifest.txt"

cleanup() {
  rm -rf "$STAGING_DIR"
}
trap cleanup EXIT

echo "Creating DB snapshot from $DB_PATH"
if command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 "$DB_PATH" ".timeout 5000" ".backup '$SNAPSHOT_DB'"
  INTEGRITY_RESULT="$(sqlite3 "$SNAPSHOT_DB" "PRAGMA integrity_check;" | tr -d '[:space:]')"
  if [[ "$INTEGRITY_RESULT" != "ok" ]]; then
    echo "ERROR: snapshot integrity check failed: $INTEGRITY_RESULT"
    exit 1
  fi
else
  echo "sqlite3 not found; falling back to file copy snapshot"
  cp "$DB_PATH" "$SNAPSHOT_DB"
fi

cat > "$MANIFEST_FILE" <<EOF
created_at_utc=$TIMESTAMP_ISO
source_db_path=$DB_PATH
sqlite_integrity_check=ok
EOF

tar -C "$STAGING_DIR" -czf "$ARCHIVE_PATH" database.db manifest.txt

ARCHIVE_SHA256="$(sha256sum "$ARCHIVE_PATH" | awk '{print $1}')"
ARCHIVE_SIZE_BYTES="$(wc -c < "$ARCHIVE_PATH" | tr -d '[:space:]')"
echo "Backup archive created: $ARCHIVE_PATH"
echo "sha256: $ARCHIVE_SHA256"

if [[ -n "$S3_URI" ]]; then
  if ! command -v aws >/dev/null 2>&1; then
    echo "ERROR: SEATSEEKER_BACKUP_S3_URI is set but aws CLI is unavailable"
    exit 1
  fi

  S3_URI="${S3_URI%/}"
  echo "Uploading backup to $S3_URI/$ARCHIVE_NAME"
  aws s3 cp "$ARCHIVE_PATH" "$S3_URI/$ARCHIVE_NAME"

  if [[ "$REMOTE_RETENTION_COUNT" =~ ^[0-9]+$ ]] && (( REMOTE_RETENTION_COUNT > 0 )); then
    remote_archives=()
    while IFS= read -r archive_name; do
      remote_archives+=("$archive_name")
    done < <(aws s3 ls "$S3_URI/" | awk '{print $4}' | grep -E '^database-.*\.tar\.gz$' | sort)
    if (( ${#remote_archives[@]} > REMOTE_RETENTION_COUNT )); then
      delete_count=$(( ${#remote_archives[@]} - REMOTE_RETENTION_COUNT ))
      for old_archive in "${remote_archives[@]:0:delete_count}"; do
        aws s3 rm "$S3_URI/$old_archive"
      done
    fi
  fi
fi

if [[ "$RETENTION_COUNT" =~ ^[0-9]+$ ]] && (( RETENTION_COUNT > 0 )); then
  local_archives=()
  while IFS= read -r archive_path; do
    local_archives+=("$archive_path")
  done < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'database-*.tar.gz' | sort)
  if (( ${#local_archives[@]} > RETENTION_COUNT )); then
    delete_count=$(( ${#local_archives[@]} - RETENTION_COUNT ))
    for old_archive in "${local_archives[@]:0:delete_count}"; do
      rm -f "$old_archive"
    done
  fi
fi

last_restore_test_at="never"
if [[ -f "$STATUS_FILE" ]]; then
  last_restore_test_at="$(grep '^LAST_RESTORE_TEST_AT=' "$STATUS_FILE" | cut -d'=' -f2- || true)"
  if [[ -z "$last_restore_test_at" ]]; then
    last_restore_test_at="never"
  fi
fi

cat > "$STATUS_FILE" <<EOF
LAST_BACKUP_AT=$TIMESTAMP_ISO
LAST_BACKUP_FILE=$ARCHIVE_NAME
LAST_BACKUP_SHA256=$ARCHIVE_SHA256
LAST_BACKUP_SIZE_BYTES=$ARCHIVE_SIZE_BYTES
LAST_RESTORE_TEST_AT=$last_restore_test_at
EOF

echo "Backup status file updated: $STATUS_FILE"
