from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from db import get_db as open_db
from db import init_db, is_postgres, resolve_sqlite_path

APP_STARTED_AT = datetime.now(timezone.utc)
SQLITE_DB_PATH = resolve_sqlite_path()
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
CRN_RE = re.compile(r"^\d{5}$")
MAX_CRNS_PER_EMAIL = 10
MAX_REQUEST_BODY_BYTES = int(os.getenv("MAX_REQUEST_BODY_BYTES", "16384"))
SUBSCRIPTION_POST_RATE = os.getenv("SUBSCRIPTION_POST_RATE", "10 per minute")
SUBSCRIPTION_DELETE_RATE = os.getenv("SUBSCRIPTION_DELETE_RATE", "20 per minute")
GLOBAL_RATE_LIMIT = os.getenv("GLOBAL_RATE_LIMIT", "120 per minute")
EXPOSE_INTERNAL_ERRORS = os.getenv("EXPOSE_INTERNAL_ERRORS", "").strip().lower() in {
    "1",
    "true",
    "yes",
}
logger = logging.getLogger("seatseeker.app")


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db():
    return open_db(None if is_postgres() else SQLITE_DB_PATH)


def build_overview_payload(conn) -> Dict[str, Any]:
    total_subscriptions = conn.execute(
        "SELECT COUNT(*) AS total FROM subscriptions"
    ).fetchone()["total"]
    total_profiles = conn.execute(
        "SELECT COUNT(DISTINCT email) AS total FROM subscriptions"
    ).fetchone()["total"]
    unique_courses = conn.execute(
        "SELECT COUNT(DISTINCT crn) AS total FROM subscriptions"
    ).fetchone()["total"]

    status_counts_rows = conn.execute(
        "SELECT status, COUNT(*) as total FROM subscriptions GROUP BY status"
    ).fetchall()
    status_counts = {row["status"]: row["total"] for row in status_counts_rows}

    last_checked = conn.execute(
        "SELECT MAX(last_checked) AS last_checked FROM subscriptions"
    ).fetchone()["last_checked"]

    return {
        "total_subscriptions": total_subscriptions,
        "total_profiles": total_profiles,
        "total_courses": unique_courses,
        "status_counts": status_counts,
        "last_checked": last_checked,
        "generated_at": now_iso_utc(),
    }


app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BODY_BYTES
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[GLOBAL_RATE_LIMIT],
    storage_uri="memory://",
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    db_ok = True
    db_error = None
    try:
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
    except Exception as exc:
        db_ok = False
        db_error = str(exc) if EXPOSE_INTERNAL_ERRORS else "database connection failed"

    status = "ok" if db_ok else "degraded"
    code = 200 if db_ok else 503

    return (
        jsonify(
            {
                "status": status,
                "service": "seatseeker",
                "db_ok": db_ok,
                "db_error": db_error,
                "uptime_seconds": int((datetime.now(timezone.utc) - APP_STARTED_AT).total_seconds()),
                "time": now_iso_utc(),
            }
        ),
        code,
    )


@app.route("/api/metrics", methods=["GET"])
def metrics():
    conn = get_db()
    try:
        return jsonify(build_overview_payload(conn))
    finally:
        conn.close()


@app.route("/api/subscriptions", methods=["GET"])
def get_subscriptions():
    conn = get_db()
    subscriptions = conn.execute(
        """
        SELECT * FROM subscriptions
        ORDER BY created_at DESC
        """
    ).fetchall()
    conn.close()

    grouped_subscriptions: Dict[str, List[Dict[str, Any]]] = {}
    for sub in subscriptions:
        sub_dict = dict(sub)
        email = sub_dict["email"]
        grouped_subscriptions.setdefault(email, []).append(sub_dict)

    return jsonify(grouped_subscriptions)


@app.route("/api/subscriptions", methods=["POST"])
@limiter.limit(SUBSCRIPTION_POST_RATE)
def create_subscription():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    crns = data.get("crns")

    if not email or not isinstance(crns, list) or not crns:
        return jsonify({"error": "Email and list of CRNs are required"}), 400

    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email format"}), 400

    cleaned_crns: List[str] = []
    for crn in crns:
        normalized = str(crn).strip()
        if not normalized:
            continue
        if not CRN_RE.match(normalized):
            return jsonify({"error": "Each CRN must be a 5-digit number"}), 400
        if normalized not in cleaned_crns:
            cleaned_crns.append(normalized)

    if not cleaned_crns:
        return jsonify({"error": "At least one valid CRN is required"}), 400

    if len(cleaned_crns) > MAX_CRNS_PER_EMAIL:
        return jsonify({"error": f"You can submit up to {MAX_CRNS_PER_EMAIL} CRNs at once"}), 400

    conn = get_db()
    inserted = 0
    try:
        if is_postgres():
            existing_rows = conn.execute(
                """
                SELECT crn
                FROM subscriptions
                WHERE email = %s
                """,
                (email,),
            ).fetchall()
        else:
            existing_rows = conn.execute(
                """
                SELECT crn
                FROM subscriptions
                WHERE email = ?
                """,
                (email,),
            ).fetchall()
        existing_crns = {str(row["crn"]) for row in existing_rows}
        new_crns = [crn for crn in cleaned_crns if crn not in existing_crns]

        if len(existing_crns) + len(new_crns) > MAX_CRNS_PER_EMAIL:
            return (
                jsonify(
                    {
                        "error": (
                            f"Hard limit is {MAX_CRNS_PER_EMAIL} total CRNs per email. "
                            f"You currently have {len(existing_crns)} in line."
                        )
                    }
                ),
                400,
            )

        current_time = now_iso_utc()
        for crn in new_crns:
            if is_postgres():
                cur = conn.execute(
                    """
                    INSERT INTO subscriptions (email, crn, last_checked)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (email, crn) DO NOTHING
                    """,
                    (email, crn, current_time),
                )
            else:
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO subscriptions
                    (email, crn, last_checked)
                    VALUES (?, ?, ?)
                    """,
                    (email, crn, current_time),
                )
            inserted += cur.rowcount
        conn.commit()
        return (
            jsonify(
                {
                    "message": "Subscriptions created successfully",
                    "inserted": inserted,
                    "ignored_duplicates": len(cleaned_crns) - len(new_crns),
                }
            ),
            201,
        )
    except Exception as exc:
        logger.exception("Failed to create subscription: %s", exc)
        return jsonify({"error": "Unable to create subscription"}), 400
    finally:
        conn.close()


@app.route("/api/subscriptions", methods=["DELETE"])
@limiter.limit(SUBSCRIPTION_DELETE_RATE)
def delete_subscription():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    crn = data.get("crn")

    if not email or not crn:
        return jsonify({"error": "Email and CRN are required"}), 400

    conn = get_db()
    try:
        if is_postgres():
            cur = conn.execute(
                """
                DELETE FROM subscriptions
                WHERE email = %s AND crn = %s
                """,
                (email, str(crn).strip()),
            )
        else:
            cur = conn.execute(
                """
                DELETE FROM subscriptions
                WHERE email = ? AND crn = ?
                """,
                (email, str(crn).strip()),
            )
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"message": "No subscription found for given email and CRN"}), 404
        return jsonify({"message": "Subscription removed successfully"})
    except Exception as exc:
        logger.exception("Failed to delete subscription: %s", exc)
        return jsonify({"error": "Unable to remove subscription"}), 400
    finally:
        conn.close()


init_db(SQLITE_DB_PATH)

if __name__ == "__main__":
    app.run(debug=False, port=5000)
