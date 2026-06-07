import sys
import os
import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

app = Flask(__name__)
MODULE_NAME = "Module_14_MultiSession"
PORT = 5014

@app.route("/api/module14/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

@app.route("/api/module14/register-session", methods=["POST"])
@jwt_required
def register_session():
    """Called after login — registers active session."""
    data    = request.get_json() or {}
    user    = request.user_payload
    db      = get_db()
    now     = datetime.datetime.utcnow()
    token   = request.headers.get("Authorization", "").split(" ", 1)[-1]
    session_id = user.get("session_id")

    # Check for existing active sessions
    existing = list(db["active_sessions"].find({
        "user_id": user["user_id"],
        "active":  True,
        "session_id": {"$ne": session_id}
    }))

    if existing:
        # Multiple session detected!
        send_log(MODULE_NAME, "SECURITY", user["user_id"], data.get("exam_id",""),
                 "multiple_session_detected",
                 {"existing_sessions": len(existing), "new_ip": request.remote_addr})

        # Invalidate old sessions
        db["active_sessions"].update_many(
            {
                "user_id": user["user_id"],
                "active": True,
                "session_id": {"$ne": session_id}
            },
            {"$set": {"active": False, "terminated_at": now.isoformat()+"Z", "reason": "new_session_detected"}}
        )
        for previous in existing:
            previous_token = previous.get("token")
            if previous_token:
                db["blacklisted_tokens"].update_one(
                    {"token": previous_token},
                    {"$set": {
                        "token": previous_token,
                        "user_id": user["user_id"],
                        "invalidated_at": now.isoformat() + "Z",
                        "reason": "new_session_detected"
                    }},
                    upsert=True
                )

    # Register new session
    db["active_sessions"].update_one(
        {"user_id": user["user_id"], "session_id": session_id},
        {"$set": {
            "user_id":    user["user_id"],
            "session_id": session_id,
            "token":      token,
            "exam_id":    data.get("exam_id", ""),
            "ip_address": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", ""),
            "started_at": now.isoformat() + "Z",
            "active":     True
        }},
        upsert=True
    )

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
        {"user_id": user["user_id"], "active": True},
        {"_id": 0, "token": 0}
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
@role_required(["teacher"])
def risk_data():
    user_id = request.args.get("user_id")
    exam_id = request.args.get("exam_id")
    if not user_id or not exam_id:
        return error_response(400, "user_id and exam_id required")

    db    = get_db()
    count = db["active_sessions"].count_documents({"user_id": user_id, "active": True})

    return success_response(data={"module": MODULE_NAME, "data": [{
        "user_id": user_id, "exam_id": exam_id,
        "timestamp": datetime.datetime.utcnow().isoformat()+"Z",
        "metric": "active_session_count", "value": count
    }]}, message="Risk data retrieved")

if __name__ == "__main__":
    print(f"Module 14 — Multi-Session Detection running on port {PORT}")
    app.run(port=PORT, debug=True)
