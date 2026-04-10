#!/usr/bin/env bash
set -Eeuo pipefail

# Safe deploy for SeatSeeker on EC2:
# 1) fetch + fast-forward pull
# 2) install dependencies in project venv
# 3) run tests
# 4) restart services only if tests pass

TARGET_BRANCH="${1:-main}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_DIR="$REPO_DIR/main"
VENV_DIR="$APP_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python3"
PIP_BIN="$VENV_DIR/bin/pip"

echo "== SeatSeeker Safe Deploy =="
echo "Repo:   $REPO_DIR"
echo "Branch: $TARGET_BRANCH"

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is not installed."
  exit 1
fi

if ! command -v sudo >/dev/null 2>&1; then
  echo "ERROR: sudo is not installed."
  exit 1
fi

cd "$REPO_DIR"

echo "== Fetching latest origin refs =="
git fetch origin

echo "== Checking out $TARGET_BRANCH =="
git checkout "$TARGET_BRANCH"

echo "== Pulling with fast-forward only =="
git pull --ff-only origin "$TARGET_BRANCH"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "ERROR: venv python not found at $PYTHON_BIN"
  echo "Create venv first: cd $APP_DIR && python3 -m venv venv"
  exit 1
fi

echo "== Installing dependencies in venv =="
"$PIP_BIN" install -r "$APP_DIR/requirements.txt"

echo "== Running test suite =="
"$PYTHON_BIN" -m pytest -q

echo "== Restarting services (tests passed) =="
sudo systemctl restart seatseeker-dashboard
sudo systemctl restart seatseeker-scheduler

echo "== Service status =="
sudo systemctl status seatseeker-dashboard --no-pager | sed -n '1,8p'
sudo systemctl status seatseeker-scheduler --no-pager | sed -n '1,8p'

echo "== Local health check =="
curl -sS -i http://127.0.0.1:5000/api/health | sed -n '1,12p'

echo "Safe deploy completed successfully."

