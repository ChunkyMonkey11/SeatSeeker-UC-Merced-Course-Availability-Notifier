from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

DEFAULT_DATABASE_PATH = Path(__file__).parent / "database.db"
ENV_PATH = Path(__file__).parent / ".env"

# Load project-local environment variables for runtime commands.
# Tests set PYTEST_CURRENT_TEST and should stay isolated from developer .env values.
if not os.getenv("PYTEST_CURRENT_TEST"):
    load_dotenv(dotenv_path=ENV_PATH)


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


def is_postgres() -> bool:
    return get_database_url().startswith(("postgres://", "postgresql://"))


def resolve_sqlite_path() -> Path:
    configured = os.getenv("DATABASE_PATH")
    if configured:
        return Path(__file__).parent / configured
    return DEFAULT_DATABASE_PATH


SQLITE_DATABASE_PATH = resolve_sqlite_path()


def get_db(sqlite_path: Optional[Path] = None):
    if is_postgres():
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(get_database_url(), row_factory=dict_row)

    conn = sqlite3.connect(sqlite_path or SQLITE_DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(sqlite_path: Optional[Path] = None) -> None:
    if is_postgres():
        conn = get_db(sqlite_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id BIGSERIAL PRIMARY KEY,
                    email TEXT NOT NULL,
                    crn TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    last_checked TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(email, crn)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_subscriptions_crn ON subscriptions (crn)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_subscriptions_email ON subscriptions (email)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions (status)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS priority_holds (
                    crn TEXT PRIMARY KEY,
                    hold_until TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_priority_holds_hold_until ON priority_holds (hold_until)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    id BIGSERIAL PRIMARY KEY,
                    email TEXT NOT NULL,
                    crn TEXT NOT NULL,
                    sent_at TIMESTAMPTZ NOT NULL,
                    source TEXT DEFAULT 'scheduler'
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sent_notifications_email ON sent_notifications (email)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sent_notifications_crn ON sent_notifications (crn)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sent_notifications_sent_at ON sent_notifications (sent_at)"
            )
            conn.commit()
        finally:
            conn.close()
        return

    path = sqlite_path or SQLITE_DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                crn TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                last_checked TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(email, crn)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS priority_holds (
                crn TEXT PRIMARY KEY,
                hold_until TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_priority_holds_hold_until ON priority_holds (hold_until)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                crn TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                source TEXT DEFAULT 'scheduler'
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sent_notifications_email ON sent_notifications (email)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sent_notifications_crn ON sent_notifications (crn)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sent_notifications_sent_at ON sent_notifications (sent_at)"
        )
        conn.commit()
    finally:
        conn.close()
