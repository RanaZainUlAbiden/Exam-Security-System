# module_02/app.py
# MODULE 02: SECURE SESSION MANAGEMENT
# JWT validation + Session blacklisting + Expiry enforcement
# PORT: 5002

import sys, os, datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from shared.jwt_helper import jwt_required, validate_token
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
MODULE_NAME = "Module_02_SecureSession"
PORT = 5002

@app.route("/api/module02/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

@app.route("/api/module02/validate-session", methods=["POST"])
@jwt_required
def validate_session():
    """Validate JWT and check it's not blacklisted."""
    user = request.user_payload
    db = get_db()

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ")[1] if " " in auth_header else ""

    # Check blacklist
    blacklisted = db["blacklisted_tokens"].find_one({"token": token})
    if blacklisted:
        send_log(MODULE_NAME, "SECURITY", user["user_id"], "", "blacklisted_token_used", {})
        return error_response(401, "Session has been invalidated. Please login again.")

    # Update last active
    db["sessions"].update_one(
        {"session_id": user.get("session_id")},
        {"$set": {"last_active": datetime.datetime.utcnow().isoformat() + "Z"}},
        upsert=True
    )

    send_log(MODULE_NAME, "INFO", user["user_id"], "", "session_validated", {"role": user["role"]})

    return success_response(
        data={"valid": True, "user_id": user["user_id"], "role": user["role"],
              "session_id": user.get("session_id"), "expires": str(user.get("exp"))},
        message="Session is valid"
    )

@app.route("/api/module02/invalidate-session", methods=["POST"])
@jwt_required
def invalidate_session():
    """Logout — blacklist the current JWT token."""
    user = request.user_payload
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ")[1] if " " in auth_header else ""
    db = get_db()

    db["blacklisted_tokens"].insert_one({
        "token": token,
        "user_id": user["user_id"],
        "invalidated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "reason": request.get_json(silent=True, force=True) and request.get_json().get("reason", "logout") or "logout"
    })

    db["sessions"].update_one(
        {"session_id": user.get("session_id")},
        {"$set": {"active": False, "ended_at": datetime.datetime.utcnow().isoformat() + "Z"}}
    )

    send_log(MODULE_NAME, "INFO", user["user_id"], "", "session_invalidated", {"session_id": user.get("session_id")})
    return success_response(data={}, message="Session invalidated. Logged out successfully.")

@app.route("/api/module02/session-status", methods=["GET"])
@jwt_required
def session_status():
    """Check if current session is active and not expired."""
    user = request.user_payload
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ")[1] if " " in auth_header else ""
    db = get_db()

    blacklisted = db["blacklisted_tokens"].find_one({"token": token})
    if blacklisted:
        return error_response(401, "Session is blacklisted")

    exp_timestamp = user.get("exp", 0)
    now_timestamp = datetime.datetime.utcnow().timestamp()
    remaining_seconds = max(0, int(exp_timestamp - now_timestamp))

    return success_response(
        data={"active": True, "user_id": user["user_id"], "role": user["role"],
              "remaining_seconds": remaining_seconds,
              "expires_in": f"{remaining_seconds // 60} minutes"},
        message="Session active"
    )

@app.route("/api/module02/risk-data", methods=["GET"])
@jwt_required
def risk_data():
    user_id = request.args.get("user_id")
    exam_id = request.args.get("exam_id")
    if not user_id or not exam_id:
        return error_response(400, "user_id and exam_id required")
    return success_response(data={"module": MODULE_NAME, "data": [{"user_id": user_id, "exam_id": exam_id, "timestamp": datetime.datetime.utcnow().isoformat()+"Z", "metric": "session_violations", "value": 0}]}, message="Risk data retrieved")

if __name__ == "__main__":
    print(f"Module 02 — Secure Session running on port {PORT}")
    app.run(port=PORT, debug=True)
