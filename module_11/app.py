# module_11/app.py
# MODULE 11: CLIPBOARD MONITORING — Prevent data leakage
# PORT: 5011

import sys, os, datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from shared.jwt_helper import jwt_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
MODULE_NAME = "Module_11_ClipboardMonitor"
PORT = 5011

@app.route("/api/module11/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

@app.route("/api/module11/clipboard-event", methods=["POST"])
@jwt_required
def clipboard_event():
    """Called by frontend on copy/paste/cut events."""
    data = request.get_json()
    if not data or "exam_id" not in data or "event_type" not in data:
        return error_response(400, "exam_id and event_type required")

    if data["event_type"] not in ["copy", "paste", "cut"]:
        return error_response(400, "event_type must be: copy, paste, or cut")

    user    = request.user_payload
    exam_id = data["exam_id"]
    db      = get_db()
    now     = datetime.datetime.utcnow()

    db["clipboard_events"].insert_one({
        "user_id":    user["user_id"],
        "exam_id":    exam_id,
        "event_type": data["event_type"],
        "content_length": data.get("content_length", 0),  # don't store actual content
        "source":     data.get("source", "unknown"),       # "question_area", "answer_area"
        "timestamp":  now.isoformat() + "Z"
    })

    # Count paste events — most suspicious
    paste_count = db["clipboard_events"].count_documents({
        "user_id": user["user_id"], "exam_id": exam_id, "event_type": "paste"
    })
    copy_count = db["clipboard_events"].count_documents({
        "user_id": user["user_id"], "exam_id": exam_id, "event_type": "copy"
    })

    level = "SECURITY" if paste_count > 0 else "WARNING"
    send_log(MODULE_NAME, level, user["user_id"], exam_id,
             f"clipboard_{data['event_type']}_detected",
             {"paste_count": paste_count, "copy_count": copy_count})

    return success_response(
        data={"event_type": data["event_type"], "paste_count": paste_count, "copy_count": copy_count},
        message="Clipboard event recorded"
    )

@app.route("/api/module11/risk-data", methods=["GET"])
@jwt_required
def risk_data():
    user_id = request.args.get("user_id")
    exam_id = request.args.get("exam_id")
    if not user_id or not exam_id:
        return error_response(400, "user_id and exam_id required")

    db = get_db()
    paste_count = db["clipboard_events"].count_documents({"user_id": user_id, "exam_id": exam_id, "event_type": "paste"})
    copy_count  = db["clipboard_events"].count_documents({"user_id": user_id, "exam_id": exam_id, "event_type": "copy"})

    return success_response(data={"module": MODULE_NAME, "data": [
        {"user_id": user_id, "exam_id": exam_id, "timestamp": datetime.datetime.utcnow().isoformat()+"Z", "metric": "paste_count", "value": paste_count},
        {"user_id": user_id, "exam_id": exam_id, "timestamp": datetime.datetime.utcnow().isoformat()+"Z", "metric": "copy_count",  "value": copy_count}
    ]}, message="Risk data retrieved")

if __name__ == "__main__":
    print(f"Module 11 — Clipboard Monitor running on port {PORT}")
    app.run(port=PORT, debug=True)
