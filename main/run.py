#!/usr/bin/env python3
"""SeatSeeker launcher for dashboard, scheduler, and setup tasks."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv


def check_dependencies() -> bool:
    required_packages = ["flask", "requests", "dotenv"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"- {package}")
        print("Install with: pip install -r requirements.txt")
        return False

    return True


def start_dashboard(port: int = 5000, debug: bool = False) -> None:
    from app import app

    print(f"Starting dashboard on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)


def start_scheduler(interval: Optional[int] = None) -> None:
    from checker_service import main

    chosen_interval = interval if interval else None
    print(f"Starting scheduler (interval={chosen_interval or 'env CHECK_INTERVAL'})")
    main(interval_override=chosen_interval)


def run_scheduler_once() -> None:
    from checker_service import check_availability

    result = check_availability()
    print("Scheduler run completed:")
    for key, value in result.items():
        print(f"- {key}: {value}")


def setup_database() -> None:
    from app import init_db

    init_db()
    print("Database initialized")


def show_status() -> None:
    database_url = os.getenv("DATABASE_URL", "").strip()
    db_path = Path(__file__).parent / os.getenv("DATABASE_PATH", "database.db")
    env_path = Path(__file__).parent / ".env"

    print("SeatSeeker status")
    print("-" * 40)
    if database_url:
        parsed = urlparse(database_url)
        host = parsed.hostname or "unknown-host"
        db_name = parsed.path.lstrip("/") or "unknown-db"
        print("Database backend: postgres")
        print(f"Database host: {host}")
        print(f"Database name: {db_name}")
    else:
        print("Database backend: sqlite")
        print(f"Database path: {db_path}")
        print(f"Database exists: {'yes' if db_path.exists() else 'no'}")
    print(f".env exists: {'yes' if env_path.exists() else 'no'}")
    print(f"TERM_CODE: {os.getenv('TERM_CODE', '202630 (default)')}")
    print(f"CHECK_INTERVAL: {os.getenv('CHECK_INTERVAL', '300 (default)')}")
    print(f"NOTIFY_MODE: {os.getenv('NOTIFY_MODE', 'all (default)')}")
    print(f"NOTIFY_BATCH_SIZE: {os.getenv('NOTIFY_BATCH_SIZE', '0 (default)')}")
    print(f"PRIORITY_HOLD_MINUTES: {os.getenv('PRIORITY_HOLD_MINUTES', '60 (default)')}")
    print(
        f"PRIORITY_EMAILS configured: "
        f"{'yes' if os.getenv('PRIORITY_EMAILS', '').strip() else 'no'}"
    )
    print(
        f"PRIORITY_EMAILS_BY_CRN configured: "
        f"{'yes' if os.getenv('PRIORITY_EMAILS_BY_CRN', '').strip() else 'no'}"
    )
    print("Health endpoint: GET /api/health")
    print("Metrics endpoint: GET /api/metrics")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SeatSeeker launcher")
    parser.add_argument(
        "command",
        choices=["dashboard", "scheduler", "scheduler-once", "setup", "status"],
        help="Command to run",
    )
    parser.add_argument("--port", type=int, default=5000, help="Dashboard port")
    parser.add_argument("--interval", type=int, default=0, help="Scheduler interval seconds")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    return parser.parse_args()


def main() -> None:
    if not check_dependencies():
        sys.exit(1)

    project_dir = Path(__file__).parent
    load_dotenv(dotenv_path=project_dir / ".env")
    os.chdir(project_dir)
    args = parse_args()

    if args.command == "dashboard":
        start_dashboard(args.port, args.debug)
    elif args.command == "scheduler":
        start_scheduler(args.interval)
    elif args.command == "scheduler-once":
        run_scheduler_once()
    elif args.command == "setup":
        setup_database()
    elif args.command == "status":
        show_status()


if __name__ == "__main__":
    main()
