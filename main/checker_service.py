from __future__ import annotations

import logging
import os
import smtplib
import time
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Set, Tuple

from dotenv import load_dotenv

from ClassChecker import ClassChecker
from db import get_db as open_db
from db import is_postgres, resolve_sqlite_path


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def normalize_email(email: str) -> str:
    return str(email).strip().lower()


def parse_priority_email_list(raw_value: str) -> Set[str]:
    emails: Set[str] = set()
    if not raw_value:
        return emails

    normalized = raw_value.replace("|", ",").replace(" ", ",")
    for item in normalized.split(","):
        email = normalize_email(item)
        if email:
            emails.add(email)
    return emails


def parse_priority_email_map(raw_value: str) -> Dict[str, Set[str]]:
    mapping: Dict[str, Set[str]] = {}
    if not raw_value:
        return mapping

    for token in raw_value.split(";"):
        token = token.strip()
        if not token or ":" not in token:
            continue

        crn_raw, emails_raw = token.split(":", 1)
        crn = str(crn_raw).strip()
        if not crn:
            continue

        emails = parse_priority_email_list(emails_raw)
        if emails:
            mapping.setdefault(crn, set()).update(emails)

    return mapping


def to_utc_datetime(value) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


# Keep test runs isolated from developer .env values (especially DATABASE_URL).
if not os.getenv("PYTEST_CURRENT_TEST"):
    load_dotenv()
SQLITE_DB_PATH = resolve_sqlite_path()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = env_int("SMTP_PORT", 465)
CHECK_INTERVAL = env_int("CHECK_INTERVAL", 300)
ERROR_RETRY_INTERVAL = env_int("ERROR_RETRY_INTERVAL", 600)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
NOTIFY_MODE = os.getenv("NOTIFY_MODE", "all").strip().lower()
NOTIFY_BATCH_SIZE = env_int("NOTIFY_BATCH_SIZE", 0)
PRIORITY_HOLD_MINUTES = max(env_int("PRIORITY_HOLD_MINUTES", 60), 0)
PRIORITY_EMAILS = parse_priority_email_list(os.getenv("PRIORITY_EMAILS", ""))
PRIORITY_EMAILS_BY_CRN = parse_priority_email_map(os.getenv("PRIORITY_EMAILS_BY_CRN", ""))

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("seatseeker.scheduler")


def effective_notify_mode() -> str:
    if NOTIFY_MODE not in {"all", "fifo"}:
        logger.warning("Invalid NOTIFY_MODE=%s, defaulting to 'all'", NOTIFY_MODE)
        return "all"
    return NOTIFY_MODE


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db():
    return open_db(None if is_postgres() else SQLITE_DB_PATH)


def fetch_subscription_queues(conn) -> Dict[str, List[dict]]:
    rows = conn.execute(
        """
        SELECT id, email, crn, status, created_at
        FROM subscriptions
        ORDER BY crn ASC, created_at ASC, id ASC
        """
    ).fetchall()

    queues: Dict[str, List[dict]] = {}
    for row in rows:
        row_dict = dict(row)
        crn = str(row_dict["crn"])
        queues.setdefault(crn, []).append(row_dict)
    return queues


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


def is_priority_subscriber(crn: str, email: str) -> bool:
    normalized_email = normalize_email(email)
    if normalized_email in PRIORITY_EMAILS:
        return True
    return normalized_email in PRIORITY_EMAILS_BY_CRN.get(str(crn), set())


def split_queue_by_priority(crn: str, queue: List[dict]) -> Tuple[List[dict], List[dict]]:
    priority_queue: List[dict] = []
    regular_queue: List[dict] = []

    for sub in queue:
        if is_priority_subscriber(crn, sub["email"]):
            priority_queue.append(sub)
        else:
            regular_queue.append(sub)

    return priority_queue, regular_queue


def select_recipients(queue: List[dict]) -> List[dict]:
    mode = effective_notify_mode()
    if mode == "all":
        return queue
    if NOTIFY_BATCH_SIZE > 0:
        return queue[:NOTIFY_BATCH_SIZE]
    return queue[:1]


def mark_queue_pending(conn, crn: str, current_time: str) -> None:
    if is_postgres():
        conn.execute(
            """
            UPDATE subscriptions
            SET status = 'pending', last_checked = %s
            WHERE crn = %s
            """,
            (current_time, crn),
        )
    else:
        conn.execute(
            """
            UPDATE subscriptions
            SET status = 'pending', last_checked = ?
            WHERE crn = ?
            """,
            (current_time, crn),
        )


def mark_subscription_pending(conn, row_id: int, current_time: str) -> None:
    if is_postgres():
        conn.execute(
            """
            UPDATE subscriptions
            SET status = 'pending', last_checked = %s
            WHERE id = %s
            """,
            (current_time, row_id),
        )
    else:
        conn.execute(
            """
            UPDATE subscriptions
            SET status = 'pending', last_checked = ?
            WHERE id = ?
            """,
            (current_time, row_id),
        )


def mark_subscription_error(conn, row_id: int, current_time: str) -> None:
    if is_postgres():
        conn.execute(
            """
            UPDATE subscriptions
            SET status = 'error', last_checked = %s
            WHERE id = %s
            """,
            (current_time, row_id),
        )
    else:
        conn.execute(
            """
            UPDATE subscriptions
            SET status = 'error', last_checked = ?
            WHERE id = ?
            """,
            (current_time, row_id),
        )


def remove_subscription(conn, row_id: int) -> None:
    if is_postgres():
        conn.execute(
            """
            DELETE FROM subscriptions
            WHERE id = %s
            """,
            (row_id,),
        )
    else:
        conn.execute(
            """
            DELETE FROM subscriptions
            WHERE id = ?
            """,
            (row_id,),
        )


def fetch_priority_hold_until(conn, crn: str) -> Optional[datetime]:
    if is_postgres():
        row = conn.execute(
            """
            SELECT hold_until
            FROM priority_holds
            WHERE crn = %s
            """,
            (crn,),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT hold_until
            FROM priority_holds
            WHERE crn = ?
            """,
            (crn,),
        ).fetchone()

    if not row:
        return None
    return to_utc_datetime(row["hold_until"])


def upsert_priority_hold(conn, crn: str, hold_until: datetime) -> None:
    hold_until_iso = hold_until.astimezone(timezone.utc).isoformat()

    if is_postgres():
        conn.execute(
            """
            INSERT INTO priority_holds (crn, hold_until, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (crn) DO UPDATE
            SET hold_until = EXCLUDED.hold_until,
                updated_at = NOW()
            """,
            (crn, hold_until_iso),
        )
    else:
        conn.execute(
            """
            INSERT INTO priority_holds (crn, hold_until, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(crn) DO UPDATE SET
                hold_until = excluded.hold_until,
                updated_at = CURRENT_TIMESTAMP
            """,
            (crn, hold_until_iso),
        )


def delete_priority_hold(conn, crn: str) -> None:
    if is_postgres():
        conn.execute(
            """
            DELETE FROM priority_holds
            WHERE crn = %s
            """,
            (crn,),
        )
    else:
        conn.execute(
            """
            DELETE FROM priority_holds
            WHERE crn = ?
            """,
            (crn,),
        )


def send_email_notification(email: str, crn: str) -> None:
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        raise ValueError("Missing email configuration in environment variables")

    msg = MIMEText(f"Good news! Course {crn} is now available.")
    msg["Subject"] = f"Course {crn} is Available"
    msg["From"] = EMAIL_SENDER
    msg["To"] = email

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)


def check_availability() -> dict:
    checker = ClassChecker()
    open_sections = {str(crn) for crn in checker.run()}

    conn = get_db()
    current_dt = datetime.now(timezone.utc)
    current_time = current_dt.isoformat()

    checked_subscriptions = 0
    total_queues = 0
    sent_notifications = 0
    failed_notifications = 0
    pending_updates = 0
    targeted_notifications = 0
    open_crns_in_queue = 0

    priority_notifications_sent = 0
    priority_notifications_failed = 0
    deferred_non_priority = 0
    priority_holds_created = 0
    priority_holds_active = 0
    priority_holds_cleared = 0

    try:
        ensure_priority_holds_table(conn)
        queues = fetch_subscription_queues(conn)
        checked_subscriptions = sum(len(queue) for queue in queues.values())
        total_queues = len(queues)

        for crn, queue in queues.items():
            if crn not in open_sections:
                mark_queue_pending(conn, crn, current_time)
                pending_updates += len(queue)
                continue

            open_crns_in_queue += 1
            priority_queue, regular_queue = split_queue_by_priority(crn, queue)

            priority_sent_this_crn = 0
            for sub in priority_queue:
                email = sub["email"]
                row_id = int(sub["id"])
                targeted_notifications += 1
                try:
                    send_email_notification(email, crn)
                    remove_subscription(conn, row_id)
                    sent_notifications += 1
                    priority_notifications_sent += 1
                    priority_sent_this_crn += 1
                except Exception as exc:
                    failed_notifications += 1
                    priority_notifications_failed += 1
                    mark_subscription_error(conn, row_id, current_time)
                    logger.exception("Failed to send email for CRN=%s email=%s: %s", crn, email, exc)

            hold_until_dt = fetch_priority_hold_until(conn, crn)
            hold_active = hold_until_dt is not None and hold_until_dt > current_dt

            if priority_sent_this_crn > 0 and regular_queue and PRIORITY_HOLD_MINUTES > 0:
                hold_until_dt = current_dt + timedelta(minutes=PRIORITY_HOLD_MINUTES)
                upsert_priority_hold(conn, crn, hold_until_dt)
                hold_active = True
                priority_holds_created += 1

            if hold_until_dt is not None and not hold_active:
                delete_priority_hold(conn, crn)
                priority_holds_cleared += 1

            if not regular_queue:
                continue

            if hold_active:
                priority_holds_active += 1
                deferred_non_priority += len(regular_queue)
                pending_updates += len(regular_queue)
                for sub in regular_queue:
                    mark_subscription_pending(conn, int(sub["id"]), current_time)
                continue

            recipients = select_recipients(regular_queue)
            targeted_notifications += len(recipients)
            for sub in recipients:
                email = sub["email"]
                row_id = int(sub["id"])
                try:
                    send_email_notification(email, crn)
                    remove_subscription(conn, row_id)
                    sent_notifications += 1
                except Exception as exc:
                    failed_notifications += 1
                    mark_subscription_error(conn, row_id, current_time)
                    logger.exception("Failed to send email for CRN=%s email=%s: %s", crn, email, exc)

            if len(recipients) < len(regular_queue):
                for sub in regular_queue[len(recipients):]:
                    mark_subscription_pending(conn, int(sub["id"]), current_time)
                pending_updates += len(regular_queue) - len(recipients)

        conn.commit()
        result = {
            "checked_subscriptions": checked_subscriptions,
            "queues_total": total_queues,
            "open_sections_found": len(open_sections),
            "open_crns_in_queue": open_crns_in_queue,
            "queue_mode": effective_notify_mode(),
            "queue_batch_size": NOTIFY_BATCH_SIZE,
            "targeted_notifications": targeted_notifications,
            "sent_notifications": sent_notifications,
            "failed_notifications": failed_notifications,
            "pending_updates": pending_updates,
            "priority_notifications_sent": priority_notifications_sent,
            "priority_notifications_failed": priority_notifications_failed,
            "deferred_non_priority": deferred_non_priority,
            "priority_holds_created": priority_holds_created,
            "priority_holds_active": priority_holds_active,
            "priority_holds_cleared": priority_holds_cleared,
            "priority_hold_minutes": PRIORITY_HOLD_MINUTES,
            "priority_global_email_count": len(PRIORITY_EMAILS),
            "priority_crn_rule_count": len(PRIORITY_EMAILS_BY_CRN),
            "time": current_time,
        }
        logger.info("Check complete: %s", result)
        return result
    finally:
        conn.close()


def main(interval_override: Optional[int] = None):
    interval = interval_override if interval_override is not None else CHECK_INTERVAL

    while True:
        try:
            check_availability()
            time.sleep(interval)
        except Exception as exc:
            logger.exception("Scheduler loop error: %s", exc)
            time.sleep(ERROR_RETRY_INTERVAL)


if __name__ == "__main__":
    main()
