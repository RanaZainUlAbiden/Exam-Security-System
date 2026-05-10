# module_13/app.py
# MODULE 13: SECURE LOGGING — SHA-256 Log Integrity
# PORT: 5013

import sys, os, datetime, hashlib, json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from bson import ObjectId
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
MODULE_NAME = "Module_13_SecureLogging"
PORT = 5013

def compute_hash(log: dict) -> str:
    content = json.dumps({
        "module": log.get("module",""), "level": log.get("level",""),
        "user_id": log.get("user_id",""), "exam_id": log.get("exam_id",""),
        "action": log.get("action",""), "timestamp": log.get("timestamp","")
    }, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()

@app.route("/api/module13/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

@app.route("/api/module13/verify-log/<log_id>", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def verify_log(log_id):
    """Verify integrity of a single log entry using SHA-256."""
    db = get_db()
    try:
        log = db["logs"].find_one({"_id": ObjectId(log_id)})
    except:
        return error_response(400, "Invalid log_id format")

    if not log:
        return error_response(404, "Log not found")

    stored_hash   = log.get("integrity_hash", "")
    computed_hash = compute_hash(log)
    is_intact     = stored_hash == computed_hash

    if not is_intact:
        send_log(MODULE_NAME, "SECURITY", request.user_payload["user_id"], "",
                 "log_tampering_detected", {"log_id": log_id})

    return success_response(
        data={"log_id": log_id, "is_intact": is_intact,
              "stored_hash": stored_hash[:16]+"...",
              "computed_hash": computed_hash[:16]+"...",
              "tampered": not is_intact},
        message="Log integrity verified" if is_intact else "⚠️ LOG TAMPERING DETECTED"
    )

@app.route("/api/module13/integrity-report/<exam_id>", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def integrity_report(exam_id):
    """Verify all logs for an exam."""
    db   = get_db()
    logs = list(db["logs"].find({"exam_id": exam_id}))

    total    = len(logs)
    intact   = 0
    tampered = []

    for log in logs:
        stored   = log.get("integrity_hash", "")
        computed = compute_hash(log)
        if stored == computed:
            intact += 1
        else:
            tampered.append(str(log["_id"]))

    if tampered:
        send_log(MODULE_NAME, "SECURITY", request.user_payload["user_id"], exam_id,
                 "tampered_logs_found", {"count": len(tampered)})

    return success_response(
        data={"exam_id": exam_id, "total_logs": total, "intact": intact,
              "tampered_count": len(tampered), "tampered_ids": tampered,
              "integrity_percentage": round((intact/total*100), 2) if total > 0 else 100},
        message="Integrity report generated"
    )

if __name__ == "__main__":
    print(f"Module 13 — Secure Logging running on port {PORT}")
    app.run(port=PORT, debug=True)
