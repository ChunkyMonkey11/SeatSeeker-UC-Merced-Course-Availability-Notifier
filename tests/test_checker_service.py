import os
import sqlite3
import sys
import types
import json
from pathlib import Path
from unittest import mock

import pytest


ROOT = Path(__file__).resolve().parents[1] / "main"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


SCHEMA = """
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    crn TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    last_checked TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(email, crn)
)
;
CREATE TABLE priority_holds (
    crn TEXT PRIMARY KEY,
    hold_until TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
;
CREATE TABLE sent_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    crn TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    source TEXT DEFAULT 'scheduler'
)
"""


def load_checker_service_module(db_path, env_overrides=None):
    source = (ROOT / "checker_service.py").read_text()
    source = "from __future__ import annotations\n" + source
    module = types.ModuleType("checker_service_under_test")
    module.__file__ = str(ROOT / "checker_service.py")
    module.__package__ = ""

    previous_db = os.environ.get("DATABASE_PATH")
    env_overrides = env_overrides or {}
    previous_env = {key: os.environ.get(key) for key in env_overrides}
    os.environ["DATABASE_PATH"] = str(db_path)
    for key, value in env_overrides.items():
        os.environ[key] = str(value)
    try:
        exec(compile(source, str(ROOT / "checker_service.py"), "exec"), module.__dict__)
    finally:
        if previous_db is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = previous_db
        for key, old_value in previous_env.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value

    return module


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "database.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    return path


def _fetch_all_rows(path):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT email, crn, status, last_checked FROM subscriptions ORDER BY id"
        ).fetchall()


def _fetch_holds(path):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT crn, hold_until FROM priority_holds ORDER BY crn"
        ).fetchall()


def _fetch_sent_notifications(path):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT email, crn, source FROM sent_notifications ORDER BY id"
        ).fetchall()


def test_check_availability_deletes_subscription_when_email_succeeds(db_path, monkeypatch):
    checker_service = load_checker_service_module(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO subscriptions (email, crn, status) VALUES (?, ?, ?)",
            ("student@example.com", "44444", "pending"),
        )
        conn.commit()

    checker = mock.Mock()
    checker.run.return_value = {"44444"}
    send_email = mock.Mock()

    monkeypatch.setattr(checker_service, "ClassChecker", lambda: checker)
    monkeypatch.setattr(checker_service, "send_email_notification", send_email)

    checker_service.check_availability()

    send_email.assert_called_once_with("student@example.com", "44444")
    assert _fetch_all_rows(db_path) == []
    sent_rows = _fetch_sent_notifications(db_path)
    assert len(sent_rows) == 1
    assert sent_rows[0]["email"] == "student@example.com"
    assert sent_rows[0]["crn"] == "44444"
    assert sent_rows[0]["source"] == "scheduler"


def test_check_availability_marks_error_when_email_fails(db_path, monkeypatch):
    checker_service = load_checker_service_module(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO subscriptions (email, crn, status) VALUES (?, ?, ?)",
            ("student@example.com", "55555", "pending"),
        )
        conn.commit()

    checker = mock.Mock()
    checker.run.return_value = {"55555"}

    def fail_email(*_args, **_kwargs):
        raise RuntimeError("smtp failure")

    monkeypatch.setattr(checker_service, "ClassChecker", lambda: checker)
    monkeypatch.setattr(checker_service, "send_email_notification", fail_email)

    checker_service.check_availability()

    rows = _fetch_all_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["email"] == "student@example.com"
    assert rows[0]["crn"] == "55555"
    assert rows[0]["status"] == "error"
    assert rows[0]["last_checked"]
    assert _fetch_sent_notifications(db_path) == []


def test_check_availability_notifies_everyone_for_open_crn_in_all_mode(db_path, monkeypatch):
    checker_service = load_checker_service_module(
        db_path, env_overrides={"NOTIFY_MODE": "all", "NOTIFY_BATCH_SIZE": "0"}
    )

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO subscriptions (email, crn, status) VALUES (?, ?, ?)",
            [
                ("first@example.com", "60606", "pending"),
                ("second@example.com", "60606", "pending"),
            ],
        )
        conn.commit()

    checker = mock.Mock()
    checker.run.return_value = {"60606"}
    send_email = mock.Mock()

    monkeypatch.setattr(checker_service, "ClassChecker", lambda: checker)
    monkeypatch.setattr(checker_service, "send_email_notification", send_email)

    result = checker_service.check_availability()

    assert send_email.call_count == 2
    sent_pairs = {(call.args[0], call.args[1]) for call in send_email.call_args_list}
    assert sent_pairs == {
        ("first@example.com", "60606"),
        ("second@example.com", "60606"),
    }
    assert _fetch_all_rows(db_path) == []
    assert result["queues_total"] == 1
    assert result["targeted_notifications"] == 2


def test_check_availability_fifo_mode_limits_notifications_per_open_crn(db_path, monkeypatch):
    checker_service = load_checker_service_module(
        db_path, env_overrides={"NOTIFY_MODE": "fifo", "NOTIFY_BATCH_SIZE": "1"}
    )

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO subscriptions (email, crn, status) VALUES (?, ?, ?)",
            [
                ("first@example.com", "70707", "pending"),
                ("second@example.com", "70707", "pending"),
            ],
        )
        conn.commit()

    checker = mock.Mock()
    checker.run.return_value = {"70707"}
    send_email = mock.Mock()

    monkeypatch.setattr(checker_service, "ClassChecker", lambda: checker)
    monkeypatch.setattr(checker_service, "send_email_notification", send_email)

    result = checker_service.check_availability()

    send_email.assert_called_once_with("first@example.com", "70707")
    rows = _fetch_all_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["email"] == "second@example.com"
    assert rows[0]["crn"] == "70707"
    assert result["targeted_notifications"] == 1


def test_priority_recipients_are_notified_first_then_non_priority_after_hold(db_path, monkeypatch):
    checker_service = load_checker_service_module(
        db_path,
        env_overrides={
            "NOTIFY_MODE": "all",
            "PRIORITY_EMAILS_BY_CRN": "80808:vip@example.com",
            "PRIORITY_HOLD_MINUTES": "60",
        },
    )

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO subscriptions (email, crn, status) VALUES (?, ?, ?)",
            [
                ("vip@example.com", "80808", "pending"),
                ("regular@example.com", "80808", "pending"),
            ],
        )
        conn.commit()

    checker = mock.Mock()
    checker.run.return_value = {"80808"}
    send_email = mock.Mock()

    monkeypatch.setattr(checker_service, "ClassChecker", lambda: checker)
    monkeypatch.setattr(checker_service, "send_email_notification", send_email)

    first_result = checker_service.check_availability()
    send_email.assert_called_once_with("vip@example.com", "80808")
    rows_after_first = _fetch_all_rows(db_path)
    assert len(rows_after_first) == 1
    assert rows_after_first[0]["email"] == "regular@example.com"
    assert rows_after_first[0]["status"] == "pending"
    holds = _fetch_holds(db_path)
    assert len(holds) == 1
    assert holds[0]["crn"] == "80808"
    assert first_result["priority_notifications_sent"] == 1
    assert first_result["deferred_non_priority"] == 1

    checker_service.check_availability()
    assert send_email.call_count == 1

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE priority_holds SET hold_until = ? WHERE crn = ?",
            ("2000-01-01T00:00:00+00:00", "80808"),
        )
        conn.commit()

    checker_service.check_availability()
    sent_pairs = {(call.args[0], call.args[1]) for call in send_email.call_args_list}
    assert sent_pairs == {
        ("vip@example.com", "80808"),
        ("regular@example.com", "80808"),
    }


def test_send_email_notification_uses_smtp_ssl_and_sends_message(db_path):
    checker_service = load_checker_service_module(
        db_path,
        env_overrides={
            "EMAIL_SENDER": "sender@example.com",
            "EMAIL_PASSWORD": "app-password",
            "SMTP_SERVER": "smtp.example.com",
            "SMTP_PORT": "465",
        },
    )

    smtp_client = mock.Mock()
    smtp_ctx = mock.Mock()
    smtp_ctx.__enter__ = mock.Mock(return_value=smtp_client)
    smtp_ctx.__exit__ = mock.Mock(return_value=False)

    with mock.patch.object(checker_service.smtplib, "SMTP_SSL", return_value=smtp_ctx) as smtp_ssl:
        checker_service.send_email_notification("student@example.com", "12345")

    smtp_ssl.assert_called_once_with("smtp.example.com", 465)
    smtp_client.login.assert_called_once_with("sender@example.com", "app-password")
    smtp_client.send_message.assert_called_once()

    sent_msg = smtp_client.send_message.call_args.args[0]
    assert sent_msg["To"] == "student@example.com"
    assert sent_msg["From"] == "sender@example.com"
    assert sent_msg["Subject"] == "Course 12345 is Available"
    assert "Course 12345 is now available" in sent_msg.get_payload()
    assert _fetch_all_rows(db_path) == []
    assert _fetch_holds(db_path) == []


def test_send_email_notification_requires_smtp_credentials(db_path):
    checker_service = load_checker_service_module(db_path)

    with pytest.raises(ValueError, match="Missing email configuration"):
        checker_service.send_email_notification("student@example.com", "12345")


def test_check_availability_falls_back_to_all_for_invalid_notify_mode(db_path, monkeypatch):
    checker_service = load_checker_service_module(
        db_path,
        env_overrides={"NOTIFY_MODE": "broken", "NOTIFY_BATCH_SIZE": "1"},
    )

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO subscriptions (email, crn, status) VALUES (?, ?, ?)",
            [
                ("first@example.com", "90909", "pending"),
                ("second@example.com", "90909", "pending"),
            ],
        )
        conn.commit()

    checker = mock.Mock()
    checker.run.return_value = {"90909"}
    send_email = mock.Mock()

    monkeypatch.setattr(checker_service, "ClassChecker", lambda: checker)
    monkeypatch.setattr(checker_service, "send_email_notification", send_email)

    result = checker_service.check_availability()

    assert result["queue_mode"] == "all"
    assert send_email.call_count == 2
    sent_pairs = {(call.args[0], call.args[1]) for call in send_email.call_args_list}
    assert sent_pairs == {
        ("first@example.com", "90909"),
        ("second@example.com", "90909"),
    }


def test_check_availability_logs_new_open_seat_events_once_per_signature(db_path, tmp_path, monkeypatch):
    event_log_path = tmp_path / "open-seat-events.log"
    heartbeat_path = tmp_path / "poller-heartbeat.json"
    checker_service = load_checker_service_module(
        db_path,
        env_overrides={
            "OPEN_SEAT_EVENT_LOG_PATH": str(event_log_path),
            "POLLER_HEARTBEAT_PATH": str(heartbeat_path),
        },
    )

    checker_first = mock.Mock()
    checker_first.run.return_value = {"11111"}
    checker_first.open_section_signatures = {("11111", "08/26/2026")}

    checker_second = mock.Mock()
    checker_second.run.return_value = {"11111"}
    checker_second.open_section_signatures = {("11111", "08/26/2026")}

    checker_third = mock.Mock()
    checker_third.run.return_value = {"11111"}
    checker_third.open_section_signatures = {("11111", "09/02/2026")}

    checker_instances = [checker_first, checker_second, checker_third]
    monkeypatch.setattr(checker_service, "ClassChecker", lambda: checker_instances.pop(0))
    monkeypatch.setattr(checker_service, "send_email_notification", mock.Mock())

    first = checker_service.check_availability()
    second = checker_service.check_availability()
    third = checker_service.check_availability()

    assert first["new_open_sections_found"] == 1
    assert second["new_open_sections_found"] == 0
    assert third["new_open_sections_found"] == 1

    lines = [line.strip() for line in event_log_path.read_text().splitlines() if line.strip()]
    assert len(lines) == 2
    records = [json.loads(line) for line in lines]
    assert records[0]["event"] == "new_open_seat_found"
    assert records[0]["crn"] == "11111"
    assert records[0]["dataset_date"] == "08/26/2026"
    assert records[1]["dataset_date"] == "09/02/2026"


def test_poller_is_blocked_uses_heartbeat_age(db_path, tmp_path, monkeypatch):
    heartbeat_path = tmp_path / "poller-heartbeat.json"
    checker_service = load_checker_service_module(
        db_path,
        env_overrides={
            "POLLER_HEARTBEAT_PATH": str(heartbeat_path),
            "OPEN_SEAT_EVENT_LOG_PATH": str(tmp_path / "events.log"),
        },
    )

    checker = mock.Mock()
    checker.run.return_value = set()
    checker.open_section_signatures = set()
    monkeypatch.setattr(checker_service, "ClassChecker", lambda: checker)

    checker_service.check_availability()

    payload = json.loads(heartbeat_path.read_text())
    heartbeat_dt = checker_service.to_utc_datetime(payload["heartbeat_at"])
    assert heartbeat_dt is not None

    assert checker_service.poller_is_blocked(
        max_stale_seconds=60,
        now=heartbeat_dt + checker_service.timedelta(seconds=30),
    ) is False
    assert checker_service.poller_is_blocked(
        max_stale_seconds=60,
        now=heartbeat_dt + checker_service.timedelta(seconds=61),
    ) is True


def test_main_sleeps_on_success_interval(db_path, monkeypatch):
    checker_service = load_checker_service_module(db_path)

    monkeypatch.setattr(checker_service, "check_availability", mock.Mock(return_value={}))
    sleep_mock = mock.Mock(side_effect=KeyboardInterrupt())
    monkeypatch.setattr(checker_service.time, "sleep", sleep_mock)

    with pytest.raises(KeyboardInterrupt):
        checker_service.main(interval_override=12)

    sleep_mock.assert_called_once_with(12)


def test_main_sleeps_on_retry_interval_after_error(db_path, monkeypatch):
    checker_service = load_checker_service_module(db_path)

    monkeypatch.setattr(
        checker_service,
        "check_availability",
        mock.Mock(side_effect=[RuntimeError("network-down"), KeyboardInterrupt()]),
    )
    sleep_mock = mock.Mock(return_value=None)
    monkeypatch.setattr(checker_service.time, "sleep", sleep_mock)

    with pytest.raises(KeyboardInterrupt):
        checker_service.main(interval_override=12)

    sleep_mock.assert_called_once_with(checker_service.ERROR_RETRY_INTERVAL)
