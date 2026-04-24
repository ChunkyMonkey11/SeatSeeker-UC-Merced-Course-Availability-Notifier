import base64
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


def basic_auth_header(username: str, password: str):
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}"}


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


def test_get_sent_notifications_requires_admin_key(client):
    test_client, _ = client

    response = test_client.get("/api/sent-notifications")

    assert response.status_code == 403
    assert response.get_json() == {"error": "Forbidden"}


def test_get_sent_notifications_returns_recent_rows(client):
    test_client, db_path = client

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO sent_notifications (email, crn, sent_at, source) VALUES (?, ?, ?, ?)",
            [
                ("a@example.com", "11111", "2026-04-11T00:00:00+00:00", "scheduler"),
                ("b@example.com", "22222", "2026-04-11T01:00:00+00:00", "scheduler"),
                ("c@example.com", "33333", "2026-04-11T02:00:00+00:00", "scheduler"),
            ],
        )
        conn.commit()

    response = test_client.get(
        "/api/sent-notifications?limit=2",
        headers={"X-SeatSeeker-Admin-Key": "test-admin-key"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 2
    assert payload[0]["email"] == "c@example.com"
    assert payload[1]["email"] == "b@example.com"


def test_admin_ops_summary_requires_basic_auth(tmp_path):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(
        db_path,
        env_overrides={
            "ADMIN_DASHBOARD_USERNAME": "admin",
            "ADMIN_DASHBOARD_PASSWORD": "test-password",
        },
    )
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    with app_module.app.test_client() as test_client:
        response = test_client.get("/api/admin/ops-summary")

    assert response.status_code == 401
    assert "Basic realm=" in response.headers["WWW-Authenticate"]


def test_admin_ops_summary_returns_aggregated_crn_counts_without_emails(tmp_path):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(
        db_path,
        env_overrides={
            "ADMIN_DASHBOARD_USERNAME": "admin",
            "ADMIN_DASHBOARD_PASSWORD": "test-password",
        },
    )
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO subscriptions (email, crn, status, last_checked) VALUES (?, ?, ?, ?)",
            [
                ("one@example.com", "12345", "pending", "2026-04-08T00:00:00"),
                ("two@example.com", "12345", "pending", "2026-04-08T00:00:00"),
                ("three@example.com", "54321", "pending", "2026-04-08T00:00:00"),
            ],
        )
        conn.commit()

    with app_module.app.test_client() as test_client:
        response = test_client.get(
            "/api/admin/ops-summary?limit=5",
            headers=basic_auth_header("admin", "test-password"),
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total_requests"] == 3
    assert payload["unique_crns_requested"] == 2
    assert payload["top_requested_crns"] == [
        {"crn": "12345", "request_count": 2},
        {"crn": "54321", "request_count": 1},
    ]
    assert all(set(row.keys()) == {"crn", "request_count"} for row in payload["top_requested_crns"])


def test_admin_ops_dashboard_renders_without_exposing_emails(tmp_path):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(
        db_path,
        env_overrides={
            "ADMIN_DASHBOARD_USERNAME": "admin",
            "ADMIN_DASHBOARD_PASSWORD": "test-password",
        },
    )
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO subscriptions (email, crn, status, last_checked) VALUES (?, ?, ?, ?)",
            [
                ("hidden-student@example.com", "77777", "pending", "2026-04-08T00:00:00"),
                ("another-student@example.com", "77777", "pending", "2026-04-08T00:00:00"),
            ],
        )
        conn.commit()

    with app_module.app.test_client() as test_client:
        response = test_client.get(
            "/admin/ops",
            headers=basic_auth_header("admin", "test-password"),
        )

    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Most Requested CRNs" in html
    assert "77777" in html
    assert "hidden-student@example.com" not in html
    assert "another-student@example.com" not in html


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


def test_subscription_post_requires_turnstile_token_when_enabled(tmp_path):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(
        db_path,
        env_overrides={
            "TURNSTILE_ENABLED": "true",
            "TURNSTILE_SECRET_KEY": "test-secret",
            "TURNSTILE_SITE_KEY": "test-site-key",
        },
    )
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    with app_module.app.test_client() as test_client:
        response = test_client.post(
            "/api/subscriptions",
            json={"email": "student@example.com", "crns": ["11111"]},
        )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Complete CAPTCHA verification and try again"}


def test_subscription_post_rejects_invalid_turnstile_token(tmp_path, monkeypatch):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(
        db_path,
        env_overrides={
            "TURNSTILE_ENABLED": "true",
            "TURNSTILE_SECRET_KEY": "test-secret",
            "TURNSTILE_SITE_KEY": "test-site-key",
        },
    )
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"success": False, "error-codes": ["invalid-input-response"]}

    def fake_post(url, data, timeout):
        assert url == app_module.TURNSTILE_VERIFY_URL
        assert data["secret"] == "test-secret"
        assert data["response"] == "invalid-token"
        assert timeout == app_module.TURNSTILE_VERIFY_TIMEOUT_SECONDS
        return DummyResponse()

    monkeypatch.setattr(app_module.requests, "post", fake_post)

    with app_module.app.test_client() as test_client:
        response = test_client.post(
            "/api/subscriptions",
            json={
                "email": "student@example.com",
                "crns": ["11111"],
                "turnstile_token": "invalid-token",
            },
        )

    assert response.status_code == 400
    assert response.get_json() == {"error": "CAPTCHA verification failed"}


def test_subscription_post_accepts_valid_turnstile_token(tmp_path, monkeypatch):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(
        db_path,
        env_overrides={
            "TURNSTILE_ENABLED": "true",
            "TURNSTILE_SECRET_KEY": "test-secret",
            "TURNSTILE_SITE_KEY": "test-site-key",
        },
    )
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"success": True}

    monkeypatch.setattr(app_module.requests, "post", lambda *_args, **_kwargs: DummyResponse())

    with app_module.app.test_client() as test_client:
        response = test_client.post(
            "/api/subscriptions",
            json={
                "email": "student@example.com",
                "crns": ["11111"],
                "turnstile_token": "valid-token",
            },
        )

    assert response.status_code == 201
    assert response.get_json()["inserted"] == 1


@pytest.mark.parametrize(
    "env_overrides, expected_db_error",
    [
        ({}, "database connection failed"),
        ({"EXPOSE_INTERNAL_ERRORS": "true"}, "boom"),
    ],
)
def test_health_endpoint_masks_or_exposes_db_errors(
    tmp_path, monkeypatch, env_overrides, expected_db_error
):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(db_path, env_overrides=env_overrides)
    app_module.app.config.update(TESTING=True)

    def fail_db():
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module, "get_db", fail_db)

    with app_module.app.test_client() as test_client:
        response = test_client.get("/api/health")

    payload = response.get_json()
    assert response.status_code == 503
    assert payload["status"] == "degraded"
    assert payload["db_ok"] is False
    assert payload["db_error"] == expected_db_error


def test_subscription_post_returns_503_when_turnstile_is_enabled_but_not_configured(tmp_path):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(
        db_path,
        env_overrides={
            "TURNSTILE_ENABLED": "true",
            "TURNSTILE_SITE_KEY": "test-site-key",
        },
    )
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    with app_module.app.test_client() as test_client:
        response = test_client.post(
            "/api/subscriptions",
            json={"email": "student@example.com", "crns": ["11111"]},
        )

    assert response.status_code == 503
    assert response.get_json() == {"error": "CAPTCHA is not configured"}


def test_subscription_post_rejects_turnstile_network_failures(tmp_path, monkeypatch):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(
        db_path,
        env_overrides={
            "TURNSTILE_ENABLED": "true",
            "TURNSTILE_SECRET_KEY": "test-secret",
            "TURNSTILE_SITE_KEY": "test-site-key",
        },
    )
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    def fail_turnstile(*_args, **_kwargs):
        raise app_module.requests.RequestException("network down")

    monkeypatch.setattr(app_module.requests, "post", fail_turnstile)

    with app_module.app.test_client() as test_client:
        response = test_client.post(
            "/api/subscriptions",
            json={
                "email": "student@example.com",
                "crns": ["11111"],
                "turnstile_token": "valid-token",
            },
        )

    assert response.status_code == 400
    assert response.get_json() == {"error": "CAPTCHA verification failed"}

    with sqlite3.connect(db_path) as conn:
        row_count = conn.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
    assert row_count == 0


@pytest.mark.parametrize(
    "payload, expected_error",
    [
        ({}, "Email and list of CRNs are required"),
        ({"email": "bad-email", "crns": ["11111"]}, "Invalid email format"),
        (
            {"email": "student@example.com", "crns": ["1111"]},
            "Each CRN must be a 5-digit number",
        ),
        (
            {"email": "student@example.com", "crns": ["", "   "]},
            "At least one valid CRN is required",
        ),
    ],
)
def test_subscription_post_validates_bad_payloads(client, payload, expected_error):
    test_client, _ = client

    response = test_client.post("/api/subscriptions", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": expected_error}


def test_subscription_post_rejects_more_than_ten_total_crns_per_email(tmp_path):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(db_path)
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO subscriptions (email, crn, status, last_checked) VALUES (?, ?, ?, ?)",
            [
                ("student@example.com", str(10000 + idx), "pending", "2026-04-08T00:00:00")
                for idx in range(10)
            ],
        )
        conn.commit()

    with app_module.app.test_client() as test_client:
        response = test_client.post(
            "/api/subscriptions",
            json={"email": "student@example.com", "crns": ["20000"]},
        )

    assert response.status_code == 400
    assert "Hard limit is 10 total CRNs per email" in response.get_json()["error"]

    with sqlite3.connect(db_path) as conn:
        row_count = conn.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE email = ?",
            ("student@example.com",),
        ).fetchone()[0]
    assert row_count == 10


@pytest.mark.parametrize(
    "payload, expected_error",
    [
        ({"email": "student@example.com"}, "Email and CRN are required"),
        ({"crn": "11111"}, "Email and CRN are required"),
    ],
)
def test_delete_subscription_requires_email_and_crn(client, payload, expected_error):
    test_client, _ = client

    response = test_client.delete("/api/subscriptions", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": expected_error}


def test_subscription_post_respects_max_request_body_size(tmp_path):
    db_path = tmp_path / "database.db"
    app_module = load_app_module(
        db_path,
        env_overrides={"MAX_REQUEST_BODY_BYTES": "64"},
    )
    app_module.app.config.update(TESTING=True)
    app_module.init_db(db_path)

    oversized_payload = (
        '{"email":"student@example.com","crns":["11111"],"padding":"'
        + ("x" * 128)
        + '"}'
    )

    with app_module.app.test_client() as test_client:
        response = test_client.post(
            "/api/subscriptions",
            data=oversized_payload,
            content_type="application/json",
        )

    assert response.status_code == 413
