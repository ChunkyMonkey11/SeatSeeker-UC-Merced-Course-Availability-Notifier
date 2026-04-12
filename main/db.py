from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional, Set

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


def _sqlite_table_columns(conn, table_name: str) -> Set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def ensure_priority_holds_table(conn) -> None:
    if is_postgres():
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
        return

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


def ensure_sent_notifications_schema(conn) -> None:
    if is_postgres():
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_notifications (
                id BIGSERIAL PRIMARY KEY,
                email TEXT NOT NULL,
                crn TEXT NOT NULL,
                sent_at TIMESTAMPTZ NOT NULL,
                term_code TEXT,
                source TEXT DEFAULT 'scheduler'
            )
            """
        )
        conn.execute(
            "ALTER TABLE sent_notifications ADD COLUMN IF NOT EXISTS term_code TEXT"
        )
        conn.execute(
            "ALTER TABLE sent_notifications ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'scheduler'"
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
        return

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sent_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            crn TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            term_code TEXT,
            source TEXT DEFAULT 'scheduler'
        )
        """
    )
    columns = _sqlite_table_columns(conn, "sent_notifications")
    if "term_code" not in columns:
        conn.execute("ALTER TABLE sent_notifications ADD COLUMN term_code TEXT")
    if "source" not in columns:
        conn.execute(
            "ALTER TABLE sent_notifications ADD COLUMN source TEXT DEFAULT 'scheduler'"
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


def record_sent_notification(
    conn,
    email: str,
    crn: str,
    sent_at: str,
    term_code: Optional[str] = None,
    source: str = "scheduler",
) -> None:
    if is_postgres():
        conn.execute(
            """
            INSERT INTO sent_notifications (email, crn, sent_at, term_code, source)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (email, crn, sent_at, term_code, source),
        )
        return

    conn.execute(
        """
        INSERT INTO sent_notifications (email, crn, sent_at, term_code, source)
        VALUES (?, ?, ?, ?, ?)
        """,
        (email, crn, sent_at, term_code, source),
    )


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
            ensure_priority_holds_table(conn)
            ensure_sent_notifications_schema(conn)
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
        ensure_priority_holds_table(conn)
        ensure_sent_notifications_schema(conn)
        conn.commit()
    finally:
        conn.close()
