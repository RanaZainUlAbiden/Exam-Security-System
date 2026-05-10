# module_14/app.py
# MODULE 14: MULTI-SESSION DETECTION — Prevent multiple logins
# PORT: 5014
<<<<<<< Updated upstream
# =============================================

import sys
import os
import datetime
import threading
import time
=======
>>>>>>> Stashed changes

import sys, os, datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

app = Flask(__name__)
MODULE_NAME = "Module_14_MultiSession"
PORT = 5014

<<<<<<< Updated upstream
MODULE_NAME     = "Module_14_Multi_Session"
PORT            = 5014
SESSION_TIMEOUT = 10  # minutes — closes stuck sessions (app crash, network failure)
HEARTBEAT_CHECK = 5   # minutes — how often background thread checks


# =============================================
# HEALTH CHECK — MANDATORY, DO NOT REMOVE
# =============================================
=======
>>>>>>> Stashed changes
@app.route("/api/module14/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

<<<<<<< Updated upstream

# =============================================
# REGISTER SESSION
# Called by Module 1 right after login success
# POST /api/module14/register-session
# =============================================
@app.route("/api/module14/register-session", methods=["POST"])
@jwt_required
def register_session():
    """
    When a student logs in, Module 1 calls this endpoint.
    We check if they already have an active session.
    If yes  -> block them (HTTP 409)
    If no   -> save their session and allow login
    """
    user      = request.user_payload
    data      = request.json or {}
    db        = get_db()

    user_id   = user.get("user_id")
    exam_id   = data.get("exam_id", "")
    device_id = data.get("device_id", "")

    # Validate required fields
    if not device_id:
        return error_response(
            message    = "device_id is required",
            error_code = 400
        )

    # Check if active session already exists
    existing = db.devices.find_one({
        "user_id": user_id,
        "status":  "active"
    })

    if existing:
        # Log blocked attempt as SECURITY event
        send_log(
            module_name = MODULE_NAME,
            level       = "SECURITY",
            user_id     = user_id,
            exam_id     = exam_id,
            action      = "multi_session_blocked",
            details     = {
                "blocked_device_id":  device_id,
                "existing_device_id": existing.get("device_id"),
                "existing_login_at":  str(existing.get("login_at"))
            }
        )

        # Notify Module 17 risk scoring
        try:
            import requests as req
            req.post(
                "http://localhost:5017/api/module17/risk-event",
                json={
                    "module":  MODULE_NAME,
                    "user_id": user_id,
                    "exam_id": exam_id,
                    "event":   "multi_session_violation",
                    "details": {
                        "reason":          "second_login_attempt",
                        "existing_device": existing.get("device_id"),
                        "new_device":      device_id
                    }
                },
                timeout=2
            )
        except Exception:
            pass  # never crash if Module 17 is not running

        return error_response(
            message    = "Another active session already exists for this account. Only one login is allowed at a time.",
            error_code = 409
        )

    # No existing session — create new one
    now = datetime.datetime.utcnow()
    session_doc = {
        "user_id":       user_id,
        "exam_id":       exam_id,
        "device_id":     device_id,
        "status":        "active",
        "login_at":      now,
        "last_activity": now,
        "closed_at":     None,
        "close_reason":  None
    }
    db.devices.insert_one(session_doc)

    send_log(
        module_name = MODULE_NAME,
        level       = "INFO",
        user_id     = user_id,
        exam_id     = exam_id,
        action      = "session_registered",
        details     = {"device_id": device_id}
    )

    return success_response(
        data    = {
            "user_id":   user_id,
            "exam_id":   exam_id,
            "device_id": device_id,
            "login_at":  now.isoformat() + "Z"
        },
        message = "Session registered successfully."
    )
=======
@app.route("/api/module14/register-session", methods=["POST"])
@jwt_required
def register_session():
    """Called after login — registers active session."""
    data    = request.get_json() or {}
    user    = request.user_payload
    db      = get_db()
    now     = datetime.datetime.utcnow()

    # Check for existing active sessions
    existing = list(db["active_sessions"].find({
        "user_id": user["user_id"],
        "active":  True
    }))

    if existing:
        # Multiple session detected!
        send_log(MODULE_NAME, "SECURITY", user["user_id"], data.get("exam_id",""),
                 "multiple_session_detected",
                 {"existing_sessions": len(existing), "new_ip": request.remote_addr})

        # Invalidate old sessions
        db["active_sessions"].update_many(
            {"user_id": user["user_id"], "active": True},
            {"$set": {"active": False, "terminated_at": now.isoformat()+"Z", "reason": "new_session_detected"}}
        )

    # Register new session
    db["active_sessions"].insert_one({
        "user_id":    user["user_id"],
        "session_id": user.get("session_id"),
        "exam_id":    data.get("exam_id", ""),
        "ip_address": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", ""),
        "started_at": now.isoformat() + "Z",
        "active":     True
    })

    was_multi = len(existing) > 0
    return success_response(
        data={"session_registered": True, "multi_session_detected": was_multi,
              "previous_sessions_terminated": len(existing)},
        message="Session registered" + (" — Previous sessions terminated" if was_multi else "")
    )

@app.route("/api/module14/check-session", methods=["GET"])
@jwt_required
def check_session():
    """Check if user has multiple active sessions."""
    user = request.user_payload
    db   = get_db()

    sessions = list(db["active_sessions"].find(
        {"user_id": user["user_id"], "active": True}, {"_id": 0}
    ))

    is_multiple = len(sessions) > 1
    if is_multiple:
        send_log(MODULE_NAME, "SECURITY", user["user_id"], "",
                 "multiple_active_sessions_found", {"count": len(sessions)})

    return success_response(
        data={"user_id": user["user_id"], "active_sessions": len(sessions),
              "multiple_detected": is_multiple, "sessions": sessions},
        message="Session check complete"
    )

@app.route("/api/module14/risk-data", methods=["GET"])
@jwt_required
def risk_data():
    user_id = request.args.get("user_id")
    exam_id = request.args.get("exam_id")
    if not user_id or not exam_id:
        return error_response(400, "user_id and exam_id required")

    db    = get_db()
    count = db["active_sessions"].count_documents({"user_id": user_id, "active": True})
>>>>>>> Stashed changes

    return success_response(data={"module": MODULE_NAME, "data": [{
        "user_id": user_id, "exam_id": exam_id,
        "timestamp": datetime.datetime.utcnow().isoformat()+"Z",
        "metric": "active_session_count", "value": count
    }]}, message="Risk data retrieved")

# =============================================
# CHECK SESSION
# GET /api/module14/check-session?user_id=xxx
# =============================================
@app.route("/api/module14/check-session", methods=["GET"])
@jwt_required
def check_session():
    user    = request.user_payload
    db      = get_db()

    # Teachers can check any user. Students can only check themselves.
    user_id = request.args.get("user_id", user.get("user_id"))

    if user.get("role") == "student" and user_id != user.get("user_id"):
        return error_response(
            message    = "Students can only check their own session.",
            error_code = 403
        )

    existing = db.devices.find_one(
        {"user_id": user_id, "status": "active"},
        {"_id": 0, "device_id": 1, "exam_id": 1, "login_at": 1, "last_activity": 1}
    )

    if existing:
        for key in ("login_at", "last_activity"):
            if isinstance(existing.get(key), datetime.datetime):
                existing[key] = existing[key].isoformat() + "Z"

        return success_response(
            data    = {"active_session": True, "session": existing},
            message = "Active session found."
        )

    return success_response(
        data    = {"active_session": False, "session": None},
        message = "No active session found."
    )


# =============================================
# CLOSE SESSION
# POST /api/module14/close-session
# =============================================
@app.route("/api/module14/close-session", methods=["POST"])
@jwt_required
def close_session():
    """
    Called by:
      - Module 1  -> student logout
      - Module 8  -> exam submitted
      - Background thread -> session timeout
    """
    user    = request.user_payload
    data    = request.json or {}
    db      = get_db()

    user_id = user.get("user_id")
    exam_id = data.get("exam_id", "")
    reason  = data.get("reason", "logout")  # logout | submitted | timeout | force_close

    now = datetime.datetime.utcnow()

    result = db.devices.update_one(
        {"user_id": user_id, "status": "active"},
        {"$set": {
            "status":       "closed",
            "closed_at":    now,
            "close_reason": reason
        }}
    )

    if result.matched_count == 0:
        return error_response(
            message    = "No active session found to close.",
            error_code = 404
        )

    send_log(
        module_name = MODULE_NAME,
        level       = "INFO",
        user_id     = user_id,
        exam_id     = exam_id,
        action      = "session_closed",
        details     = {"reason": reason, "closed_at": now.isoformat() + "Z"}
    )

    return success_response(
        data    = {
            "user_id":   user_id,
            "exam_id":   exam_id,
            "closed_at": now.isoformat() + "Z",
            "reason":    reason
        },
        message = "Session closed successfully."
    )


# =============================================
# HEARTBEAT
# POST /api/module14/heartbeat
# Android app calls this every 5 minutes during exam
# If heartbeat stops = app crashed or network failed
# After 15 min of no heartbeat = session auto-closes
# =============================================
@app.route("/api/module14/heartbeat", methods=["POST"])
@jwt_required
def heartbeat():
    user    = request.user_payload
    db      = get_db()

    user_id = user.get("user_id")
    now     = datetime.datetime.utcnow()

    result = db.devices.update_one(
        {"user_id": user_id, "status": "active"},
        {"$set": {"last_activity": now}}
    )

    if result.matched_count == 0:
        return error_response(
            message    = "No active session found.",
            error_code = 404
        )

    return success_response(
        data    = {"last_activity": now.isoformat() + "Z"},
        message = "Heartbeat recorded."
    )


# =============================================
# RISK DATA — FOR MODULE 17
# GET /api/module14/risk-data?user_id=x&exam_id=y
# =============================================
@app.route("/api/module14/risk-data", methods=["GET"])
@jwt_required
def risk_data():
    user    = request.user_payload
    db      = get_db()

    user_id = request.args.get("user_id", user.get("user_id"))
    exam_id = request.args.get("exam_id", "")

    total_sessions = db.devices.count_documents({
        "user_id": user_id,
        "exam_id": exam_id
    })

    blocked_attempts = db.devices.count_documents({
        "user_id":      user_id,
        "exam_id":      exam_id,
        "close_reason": "force_close"
    })

    now = datetime.datetime.utcnow().isoformat() + "Z"

    return success_response(
        data = {
            "module": MODULE_NAME,
            "data": [
                {
                    "user_id":   user_id,
                    "exam_id":   exam_id,
                    "timestamp": now,
                    "metric":    "multi_session_attempt_count",
                    "value":     blocked_attempts
                },
                {
                    "user_id":   user_id,
                    "exam_id":   exam_id,
                    "timestamp": now,
                    "metric":    "total_session_count",
                    "value":     total_sessions
                }
            ]
        },
        message = "Risk data retrieved."
    )


# =============================================
# AUTO SESSION TIMEOUT — BACKGROUND THREAD
# Problem solved: app crash / network failure
# leaves session stuck as "active" forever,
# blocking the student from logging in again.
# Fix: every 5 min, close sessions idle 15+ min.
# =============================================
def close_idle_sessions():
    while True:
        try:
            db     = get_db()
            now    = datetime.datetime.utcnow()
            cutoff = now - datetime.timedelta(minutes=SESSION_TIMEOUT)

            idle = list(db.devices.find({
                "status":        "active",
                "last_activity": {"$lt": cutoff}
            }))

            for session in idle:
                db.devices.update_one(
                    {"_id": session["_id"]},
                    {"$set": {
                        "status":       "closed",
                        "closed_at":    now,
                        "close_reason": "timeout"
                    }}
                )

                send_log(
                    module_name = MODULE_NAME,
                    level       = "WARNING",
                    user_id     = session.get("user_id"),
                    exam_id     = session.get("exam_id"),
                    action      = "session_timeout",
                    details     = {
                        "device_id":     session.get("device_id"),
                        "last_activity": str(session.get("last_activity")),
                        "closed_at":     now.isoformat() + "Z"
                    }
                )

                print(f"[TIMEOUT] Session auto-closed for {session.get('user_id')} — idle 15+ min")

        except Exception as e:
            print(f"[TIMEOUT ERROR] {e}")

        time.sleep(HEARTBEAT_CHECK * 60)


# =============================================
# ENTRY POINT
# =============================================
if __name__ == "__main__":
<<<<<<< Updated upstream
    threading.Thread(target=close_idle_sessions, daemon=True).start()
    print(f"⏱  Auto timeout active — idle sessions close after {SESSION_TIMEOUT} minutes")
    print(f"🔐 Module 14 — Multi-Session Detection running on port {PORT}")
    app.run(port=PORT, debug=True)
=======
    print(f"Module 14 — Multi-Session Detection running on port {PORT}")
    app.run(port=PORT, debug=True)
>>>>>>> Stashed changes
