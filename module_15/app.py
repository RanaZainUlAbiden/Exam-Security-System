# module_15/app.py
# MODULE 15: BEHAVIORAL ANALYSIS — Rule-based anomaly detection
# PORT: 5015

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
MODULE_NAME = "Module_15_BehavioralAnalysis"
PORT = 5015

# Rule thresholds
RULES = {
    "idle_time_threshold_sec": 300,    # 5 min idle = suspicious
    "typing_speed_max_wpm":    150,     # too fast = suspicious
    "question_skip_threshold": 3,       # skipping too many questions
}

@app.route("/api/module15/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

@app.route("/api/module15/log-behavior", methods=["POST"])
@jwt_required
@role_required(["student"])
def log_behavior():
    """Log a behavioral event during exam."""
    data = request.get_json()
    if not data or "exam_id" not in data or "event_type" not in data:
        return error_response(400, "exam_id and event_type required")

    user    = request.user_payload
    db      = get_db()
    now     = datetime.datetime.utcnow()

    state_error = active_exam_error(db, user["user_id"], data["exam_id"])
    if state_error:
        return error_response(409, state_error)

    db["behavior_events"].insert_one({
        "user_id":    user["user_id"],
        "exam_id":    data["exam_id"],
        "event_type": data["event_type"],
        "value":      data.get("value", 0),
        "details":    data.get("details", {}),
        "timestamp":  now.isoformat() + "Z"
    })

    send_log(MODULE_NAME, "INFO", user["user_id"], data["exam_id"],
             f"behavior_{data['event_type']}", {"value": data.get("value", 0)})

    return success_response(data={"logged": True}, message="Behavior event logged")

@app.route("/api/module15/analyze", methods=["POST"])
@jwt_required
@role_required(["teacher"])
def analyze():
    """Run behavioral analysis for a student in an exam."""
    data = request.get_json()
    if not data or "user_id" not in data or "exam_id" not in data:
        return error_response(400, "user_id and exam_id required")

    user_id = data["user_id"]
    exam_id = data["exam_id"]
    db      = get_db()

    events  = list(db["behavior_events"].find({"user_id": user_id, "exam_id": exam_id}))

    anomalies = []
    idle_events  = [e for e in events if e["event_type"] == "idle"]
    speed_events = [e for e in events if e["event_type"] == "typing_speed"]
    skip_events  = [e for e in events if e["event_type"] == "question_skip"]

    # Rule 1: Long idle time
    total_idle = sum(e.get("value", 0) for e in idle_events)
    if total_idle > RULES["idle_time_threshold_sec"]:
        anomalies.append({"rule": "excessive_idle", "value": total_idle,
                          "threshold": RULES["idle_time_threshold_sec"]})

    # Rule 2: Typing too fast
    for e in speed_events:
        if e.get("value", 0) > RULES["typing_speed_max_wpm"]:
            anomalies.append({"rule": "abnormal_typing_speed", "value": e["value"],
                              "threshold": RULES["typing_speed_max_wpm"]})

    # Rule 3: Too many question skips
    if len(skip_events) > RULES["question_skip_threshold"]:
        anomalies.append({"rule": "excessive_question_skips", "value": len(skip_events),
                          "threshold": RULES["question_skip_threshold"]})

    if anomalies:
        send_log(MODULE_NAME, "SECURITY", user_id, exam_id,
                 "behavioral_anomalies_detected", {"anomalies": anomalies})

    # Store analysis result
    now = datetime.datetime.utcnow()
    db["behavior_analysis"].update_one(
        {"user_id": user_id, "exam_id": exam_id},
        {"$set": {"anomalies": anomalies, "total_idle_sec": total_idle,
                  "analyzed_at": now.isoformat()+"Z", "flagged": len(anomalies) > 0}},
        upsert=True
    )

    return success_response(
        data={"user_id": user_id, "exam_id": exam_id, "anomalies": anomalies,
              "flagged": len(anomalies) > 0, "total_idle_seconds": total_idle},
        message="Behavioral analysis complete"
    )

@app.route("/api/module15/risk-data", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def risk_data():
    user_id = request.args.get("user_id")
    exam_id = request.args.get("exam_id")
    if not user_id or not exam_id:
        return error_response(400, "user_id and exam_id required")

    db     = get_db()
    result = db["behavior_analysis"].find_one({"user_id": user_id, "exam_id": exam_id})
    idle   = result.get("total_idle_sec", 0) if result else 0

    return success_response(data={"module": MODULE_NAME, "data": [{
        "user_id": user_id, "exam_id": exam_id,
        "timestamp": datetime.datetime.utcnow().isoformat()+"Z",
        "metric": "idle_time_seconds", "value": idle
    }]}, message="Risk data retrieved")

if __name__ == "__main__":
    print(f"Module 15 — Behavioral Analysis running on port {PORT}")
    app.run(port=PORT, debug=True)
