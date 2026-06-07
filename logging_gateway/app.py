# logging_gateway/app.py
# =============================================
# CENTRAL LOGGING GATEWAY — PORT 5000
# DO NOT MODIFY — Managed by Integration Lead
# All modules send logs here
# =============================================

from flask import Flask, request, jsonify
from pymongo import MongoClient
import hashlib
import hmac
import datetime
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)

import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI     = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "exam_security")
LOGGING_GATEWAY_SECRET = os.getenv(
    "LOGGING_GATEWAY_SECRET",
    os.getenv("JWT_SECRET", "exam_security_UET_2024_secret_key")
)

client = MongoClient(MONGO_URI)
db     = client[DATABASE_NAME]
logs   = db["logs"]

VALID_LEVELS  = ["INFO", "WARNING", "ERROR", "SECURITY"]
VALID_MODULES = [f"Module_{str(i).zfill(2)}_" for i in range(1, 18)]


def gateway_authorized():
    supplied = request.headers.get("X-Logging-Secret", "")
    return hmac.compare_digest(supplied, LOGGING_GATEWAY_SECRET)


def compute_integrity_hash(log_entry: dict) -> str:
    """SHA-256 hash of log content for integrity verification."""
    content = json.dumps({
        "module":    log_entry["module"],
        "level":     log_entry["level"],
        "user_id":   log_entry["user_id"],
        "exam_id":   log_entry["exam_id"],
        "action":    log_entry["action"],
        "timestamp": log_entry["timestamp"]
    }, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


@app.route("/api/logs/write", methods=["POST"])
def write_log():
    """Receive log from any module and store with SHA-256 integrity hash."""
    if not gateway_authorized():
        return jsonify({
            "status": "error",
            "error_code": 401,
            "message": "Invalid logging gateway credentials"
        }), 401

    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    required_fields = ["module", "level", "user_id", "exam_id", "action", "timestamp"]
    for field in required_fields:
        if field not in data:
            return jsonify({
                "status": "error",
                "message": f"Missing required field: {field}"
            }), 400

    if data["level"] not in VALID_LEVELS:
        return jsonify({
            "status": "error",
            "message": f"Invalid level. Must be one of: {VALID_LEVELS}"
        }), 400

    log_entry = {
        "module":    data["module"],
        "level":     data["level"],
        "user_id":   data["user_id"],
        "exam_id":   data["exam_id"],
        "action":    data["action"],
        "details":   data.get("details", {}),
        "timestamp": data["timestamp"],
        "received_at": datetime.datetime.utcnow().isoformat() + "Z"
    }

    log_entry["integrity_hash"] = compute_integrity_hash(log_entry)

    logs.insert_one(log_entry)

    return jsonify({
        "status": "accepted",
        "message": "Log stored successfully"
    }), 202


@app.route("/api/logs/health", methods=["GET"])
def health():
    return jsonify({
        "module": "Logging_Gateway",
        "status": "healthy",
        "dependencies": ["mongodb"],
        "version": "1.0.0"
    }), 200


@app.route("/api/logs/verify/<log_id>", methods=["GET"])
def verify_log_integrity(log_id):
    """Verify SHA-256 integrity of a stored log."""
    if not gateway_authorized():
        return jsonify({
            "status": "error",
            "error_code": 401,
            "message": "Invalid logging gateway credentials"
        }), 401

    from bson import ObjectId
    try:
        log = logs.find_one({"_id": ObjectId(log_id)})
        if not log:
            return jsonify({"status": "error", "message": "Log not found"}), 404

        stored_hash   = log.get("integrity_hash", "")
        computed_hash = compute_integrity_hash(log)
        is_intact     = stored_hash == computed_hash

        return jsonify({
            "status": "success",
            "data": {
                "log_id":     str(log["_id"]),
                "is_intact":  is_intact,
                "stored_hash":   stored_hash,
                "computed_hash": computed_hash
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    print("🔐 Logging Gateway running on port 5000")
    app.run(port=5000, debug=True)
