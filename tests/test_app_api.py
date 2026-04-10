import os
import sqlite3
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1] / "main"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_app_module(db_path, env_overrides=None):
    source = (ROOT / "app.py").read_text()
    source = "from __future__ import annotations\n" + source
    module = types.ModuleType("app_under_test")
    module.__file__ = str(ROOT / "app.py")
    module.__package__ = ""

    previous_db = os.environ.get("DATABASE_PATH")
    env_overrides = env_overrides or {}
    previous_env = {key: os.environ.get(key) for key in env_overrides}
    os.environ["DATABASE_PATH"] = str(db_path)
    for key, value in env_overrides.items():
        os.environ[key] = str(value)
    try:
        exec(compile(source, str(ROOT / "app.py"), "exec"), module.__dict__)
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
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(
        db_path,
        env_overrides={"ADMIN_API_KEY": "test-admin-key"},
    )
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    with app_module.app.test_client() as test_client:
        yield test_client, db_path


def test_get_subscriptions_returns_grouped_empty_dict(client):
    test_client, _ = client

    response = test_client.get(
        "/api/subscriptions",
        headers={"X-SeatSeeker-Admin-Key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert response.get_json() == {}


def test_get_subscriptions_requires_admin_key(client):
    test_client, _ = client

    response = test_client.get("/api/subscriptions")

    assert response.status_code == 403
    assert response.get_json() == {"error": "Forbidden"}


def test_post_subscription_creates_grouped_subscriptions(client):
    test_client, db_path = client

    response = test_client.post(
        "/api/subscriptions",
        json={"email": "student@example.com", "crns": ["11111", "22222"]},
    )

    assert response.status_code == 201
    assert response.get_json()["message"] == "Subscriptions created successfully"
    assert response.get_json()["inserted"] == 2

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT email, crn, status FROM subscriptions ORDER BY crn"
        ).fetchall()

    assert rows == [
        ("student@example.com", "11111", "pending"),
        ("student@example.com", "22222", "pending"),
    ]

    response = test_client.get(
        "/api/subscriptions",
        headers={"X-SeatSeeker-Admin-Key": "test-admin-key"},
    )
    data = response.get_json()

    assert set(data.keys()) == {"student@example.com"}
    assert {item["crn"] for item in data["student@example.com"]} == {"11111", "22222"}


def test_metrics_endpoint_returns_profile_and_request_totals(client):
    test_client, db_path = client

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO subscriptions (email, crn, status, last_checked) VALUES (?, ?, ?, ?)",
            [
                ("a@example.com", "11111", "pending", "2026-04-08T00:00:00"),
                ("b@example.com", "11111", "pending", "2026-04-08T00:00:00"),
                ("c@example.com", "22222", "pending", "2026-04-08T00:00:00"),
            ],
        )
        conn.commit()

    response = test_client.get("/api/metrics")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["total_subscriptions"] == 3
    assert payload["total_profiles"] == 3
    assert payload["total_courses"] == 2
    assert payload["status_counts"]["pending"] == 3


def test_delete_subscription_removes_row_and_returns_404_when_missing(client):
    test_client, db_path = client

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO subscriptions (email, crn, status, last_checked) VALUES (?, ?, ?, ?)",
            ("student@example.com", "33333", "pending", "2026-04-08T00:00:00"),
        )
        conn.commit()

    response = test_client.delete(
        "/api/subscriptions",
        json={"email": "student@example.com", "crn": "33333"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"message": "Subscription removed successfully"}

    response = test_client.delete(
        "/api/subscriptions",
        json={"email": "student@example.com", "crn": "33333"},
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "message": "No subscription found for given email and CRN"
    }


def test_subscription_post_is_rate_limited(tmp_path):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(
        db_path,
        env_overrides={
            "SUBSCRIPTION_POST_RATE": "1 per minute",
            "GLOBAL_RATE_LIMIT": "100 per minute",
        },
    )
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    with app_module.app.test_client() as test_client:
        first = test_client.post(
            "/api/subscriptions",
            json={"email": "student@example.com", "crns": ["11111"]},
        )
        second = test_client.post(
            "/api/subscriptions",
            json={"email": "student2@example.com", "crns": ["22222"]},
        )

    assert first.status_code == 201
    assert second.status_code == 429
