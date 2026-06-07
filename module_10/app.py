# module_10/app.py
# MODULE 10: TAB MONITORING — Detect app/tab switching
# PORT: 5010

import sys, os, datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response
from shared.exam_state_helper import active_exam_error

import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
MODULE_NAME = "Module_10_TabMonitor"
PORT = 5010

TAB_SWITCH_LIMIT = 5  # flag student after this many switches

@app.route("/api/module10/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

@app.route("/api/module10/tab-switch", methods=["POST"])
@jwt_required
@role_required(["student"])
def tab_switch():
    """Called by frontend whenever student switches tab/app."""
    data = request.get_json()
    if not data or "exam_id" not in data:
        return error_response(400, "exam_id required")

    user    = request.user_payload
    exam_id = data["exam_id"]
    db      = get_db()
    now     = datetime.datetime.utcnow()

    state_error = active_exam_error(db, user["user_id"], exam_id)
    if state_error:
        return error_response(409, state_error)

    # Record the event
    db["tab_events"].insert_one({
        "user_id":    user["user_id"],
        "exam_id":    exam_id,
        "event_type": data.get("event_type", "tab_hidden"),  # tab_hidden / tab_visible
        "timestamp":  now.isoformat() + "Z",
        "url":        data.get("url", ""),
        "duration_away_ms": data.get("duration_away_ms", 0)
    })

    # Count total switches for this student in this exam
    count = db["tab_events"].count_documents({
        "user_id":    user["user_id"],
        "exam_id":    exam_id,
        "event_type": "tab_hidden"
    })

    level = "INFO"
    if count >= TAB_SWITCH_LIMIT:
        level = "SECURITY"

    send_log(MODULE_NAME, level, user["user_id"], exam_id,
             "tab_switch_detected", {"count": count, "limit": TAB_SWITCH_LIMIT})

    return success_response(
        data={"tab_switch_count": count, "flagged": count >= TAB_SWITCH_LIMIT},
        message="Tab switch recorded"
    )

@app.route("/api/module10/risk-data", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def risk_data():
    user_id = request.args.get("user_id")
    exam_id = request.args.get("exam_id")
    if not user_id or not exam_id:
        return error_response(400, "user_id and exam_id required")

    db    = get_db()
    count = db["tab_events"].count_documents({
        "user_id": user_id, "exam_id": exam_id, "event_type": "tab_hidden"
    })

    return success_response(data={"module": MODULE_NAME, "data": [{
        "user_id": user_id, "exam_id": exam_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "metric": "tab_switch_count", "value": count
    }]}, message="Risk data retrieved")

if __name__ == "__main__":
    print(f"Module 10 — Tab Monitor running on port {PORT}")
    app.run(port=PORT, debug=True)
