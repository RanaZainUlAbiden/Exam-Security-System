# module_12/app.py
# MODULE 12: ACTIVITY LOGGING — Complete audit trail
# PORT: 5012

import sys, os, datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

app = Flask(__name__)
MODULE_NAME = "Module_12_ActivityLogging"
PORT = 5012

VALID_ACTIONS = [
    "page_load", "question_viewed", "answer_typed", "answer_saved",
    "exam_started", "exam_paused", "exam_resumed", "focus_lost",
    "focus_gained", "right_click_attempt", "keyboard_shortcut"
]

@app.route("/api/module12/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

@app.route("/api/module12/log-activity", methods=["POST"])
@jwt_required
def log_activity():
    data = request.get_json()
    if not data or "exam_id" not in data or "action" not in data:
        return error_response(400, "exam_id and action required")

    user    = request.user_payload
    db      = get_db()
    now     = datetime.datetime.utcnow()

    activity = {
        "user_id":    user["user_id"],
        "username":   user["username"],
        "exam_id":    data["exam_id"],
        "action":     data["action"],
        "details":    data.get("details", {}),
        "ip_address": request.remote_addr,
        "timestamp":  now.isoformat() + "Z"
    }

    db["activity_logs"].insert_one(activity)

    # Flag suspicious actions
    suspicious = ["right_click_attempt", "keyboard_shortcut", "focus_lost"]
    level = "SECURITY" if data["action"] in suspicious else "INFO"

    send_log(MODULE_NAME, level, user["user_id"], data["exam_id"],
             f"activity_{data['action']}", data.get("details", {}))

    return success_response(data={"logged": True, "action": data["action"]}, message="Activity logged")

@app.route("/api/module12/get-logs/<exam_id>", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def get_logs(exam_id):
    db   = get_db()
    user_id = request.args.get("user_id")

    query = {"exam_id": exam_id}
    if user_id:
        query["user_id"] = user_id

    logs = list(db["activity_logs"].find(query, {"_id": 0}).sort("timestamp", -1).limit(200))
    return success_response(data={"exam_id": exam_id, "logs": logs, "total": len(logs)}, message="Logs retrieved")

@app.route("/api/module12/risk-data", methods=["GET"])
@jwt_required
def risk_data():
    user_id = request.args.get("user_id")
    exam_id = request.args.get("exam_id")
    if not user_id or not exam_id:
        return error_response(400, "user_id and exam_id required")

    db    = get_db()
    suspicious_actions = ["right_click_attempt", "keyboard_shortcut", "focus_lost"]
    count = db["activity_logs"].count_documents({
        "user_id": user_id, "exam_id": exam_id,
        "action": {"$in": suspicious_actions}
    })

    return success_response(data={"module": MODULE_NAME, "data": [{
        "user_id": user_id, "exam_id": exam_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "metric": "suspicious_activity_count", "value": count
    }]}, message="Risk data retrieved")

if __name__ == "__main__":
    print(f"Module 12 — Activity Logging running on port {PORT}")
    app.run(port=PORT, debug=True)
