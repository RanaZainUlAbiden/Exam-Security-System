# module_03/app.py
# =============================================
# MODULE 03: DEVICE FINGERPRINTING
# Device binding + Account sharing prevention
# PORT: 5003
# =============================================
#
# SECURITY CONCEPT:
#   Each student's account is bound to one device.
#   If they try to login from a different device,
#   the system detects and flags it.
#
# ATTACK PREVENTED:
#   - Account sharing between students
#   - Using someone else's credentials on your device
#   - Multiple students using one account
#
# HOW IT WORKS:
#   1. Student first login → device fingerprint registered
#   2. Every next login → fingerprint compared
#   3. Different device → flagged as suspicious
#   4. Teacher can view device history
#
# FINGERPRINT = SHA-256 of (user_agent + platform + screen + timezone)
# =============================================

import sys
import os
import datetime
import hashlib
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

MODULE_NAME = "Module_03_DeviceFingerprinting"
PORT        = 5003


# =============================================
# HELPER FUNCTIONS
# =============================================

def compute_fingerprint(components: dict) -> str:
    """
    Compute SHA-256 fingerprint from device components.
    Components: user_agent, platform, screen_resolution,
                timezone, language, color_depth
    """
    # Sort keys for consistent hashing
    stable_string = json.dumps(components, sort_keys=True)
    return hashlib.sha256(stable_string.encode()).hexdigest()


def get_client_ip():
    """Get real client IP, handle proxies."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "unknown"


# =============================================
# HEALTH CHECK
# =============================================

@app.route("/api/module03/health", methods=["GET"])
def health():
    return {
        "module":       MODULE_NAME,
        "status":       "healthy",
        "dependencies": ["mongodb"],
        "version":      "1.0.0"
    }, 200


# =============================================
# REGISTER DEVICE
# POST /api/module03/register-device
# Role: student
#
# Call this right after student first logs in.
#
# Request Body:
# {
#   "user_agent": "Mozilla/5.0 ...",
#   "platform": "Win32",
#   "screen_resolution": "1920x1080",
#   "timezone": "Asia/Karachi",
#   "language": "en-US",
#   "color_depth": "24"
# }
# =============================================

@app.route("/api/module03/register-device", methods=["POST"])
@jwt_required
def register_device():
    data = request.get_json()
    user = request.user_payload

    required = ["user_agent", "platform", "screen_resolution", "timezone"]
    for field in required:
        if not data or field not in data:
            return error_response(400, f"Missing field: {field}")

    db      = get_db()
    devices = db["devices"]
    users   = db["users"]

    # Build fingerprint components
    components = {
        "user_agent":        data["user_agent"],
        "platform":          data["platform"],
        "screen_resolution": data["screen_resolution"],
        "timezone":          data["timezone"],
        "language":          data.get("language", "unknown"),
        "color_depth":       data.get("color_depth", "unknown"),
    }

    fingerprint = compute_fingerprint(components)
    client_ip   = get_client_ip()
    now         = datetime.datetime.utcnow()

    # Check if user already has a registered device
    existing_device = devices.find_one({"user_id": user["user_id"]})

    if existing_device:
        # Device already registered
        if existing_device["fingerprint_hash"] == fingerprint:
            # Same device — just update last seen
            devices.update_one(
                {"user_id": user["user_id"]},
                {"$set": {
                    "last_seen":    now.isoformat() + "Z",
                    "last_ip":      client_ip,
                    "login_count":  existing_device.get("login_count", 0) + 1
                }}
            )

            send_log(MODULE_NAME, "INFO", user["user_id"], "",
                     "known_device_login", {"fingerprint": fingerprint[:16] + "..."})

            return success_response(
                data    = {
                    "status":      "known_device",
                    "verified":    True,
                    "fingerprint": fingerprint[:16] + "...",
                },
                message = "Device recognized. Access granted."
            )

        else:
            # DIFFERENT DEVICE — suspicious!
            # Log the attempt with full details
            send_log(
                module_name = MODULE_NAME,
                level       = "SECURITY",
                user_id     = user["user_id"],
                exam_id     = "",
                action      = "new_device_detected",
                details     = {
                    "registered_fingerprint": existing_device["fingerprint_hash"][:16] + "...",
                    "new_fingerprint":        fingerprint[:16] + "...",
                    "new_ip":                 client_ip,
                    "registered_ip":          existing_device.get("registered_ip"),
                    "platform":               data["platform"],
                }
            )

            # Save the suspicious attempt
            db["device_alerts"].insert_one({
                "user_id":              user["user_id"],
                "username":             user["username"],
                "registered_fp":        existing_device["fingerprint_hash"],
                "attempted_fp":         fingerprint,
                "attempted_ip":         client_ip,
                "attempted_components": components,
                "timestamp":            now.isoformat() + "Z",
                "resolved":             False
            })

            return error_response(403,
                "Device mismatch detected. This account is registered on a different device. "
                "Contact your teacher if this is a mistake."
            )

    # First time — register this device
    device_doc = {
        "user_id":           user["user_id"],
        "username":          user["username"],
        "fingerprint_hash":  fingerprint,
        "components":        components,
        "registered_ip":     client_ip,
        "registered_at":     now.isoformat() + "Z",
        "last_seen":         now.isoformat() + "Z",
        "last_ip":           client_ip,
        "login_count":       1,
        "is_active":         True
    }

    devices.insert_one(device_doc)

    # Also update user record with fingerprint hash (for JWT)
    from bson import ObjectId
    users.update_one(
        {"_id": ObjectId(user["user_id"])},
        {"$set": {"device_fingerprint_hash": fingerprint}}
    )

    send_log(MODULE_NAME, "INFO", user["user_id"], "",
             "device_registered",
             {
                 "fingerprint": fingerprint[:16] + "...",
                 "platform":    data["platform"],
                 "ip":          client_ip
             })

    return success_response(
        data    = {
            "status":          "registered",
            "verified":        True,
            "fingerprint":     fingerprint[:16] + "...",
            "registered_at":   now.isoformat() + "Z",
        },
        message = "Device registered successfully. Account bound to this device."
    )


# =============================================
# VERIFY DEVICE
# GET /api/module03/verify-device
# Role: student
#
# Quick check — is current device the registered one?
# Call this at start of every exam session.
# =============================================

@app.route("/api/module03/verify-device", methods=["POST"])
@jwt_required
def verify_device():
    data = request.get_json()
    user = request.user_payload

    required = ["user_agent", "platform", "screen_resolution", "timezone"]
    for field in required:
        if not data or field not in data:
            return error_response(400, f"Missing field: {field}")

    components  = {
        "user_agent":        data["user_agent"],
        "platform":          data["platform"],
        "screen_resolution": data["screen_resolution"],
        "timezone":          data["timezone"],
        "language":          data.get("language", "unknown"),
        "color_depth":       data.get("color_depth", "unknown"),
    }

    fingerprint = compute_fingerprint(components)

    db             = get_db()
    registered_dev = db["devices"].find_one({"user_id": user["user_id"]})

    if not registered_dev:
        return error_response(404,
            "No device registered for this account. Please register device first."
        )

    if registered_dev["fingerprint_hash"] != fingerprint:
        send_log(MODULE_NAME, "SECURITY", user["user_id"], "",
                 "device_verification_failed",
                 {"expected": registered_dev["fingerprint_hash"][:16] + "...",
                  "received": fingerprint[:16] + "..."})

        return error_response(403, "Device verification failed. Access denied.")

    # Update exam state to DEVICE_VERIFIED
    db["exams"].update_one(
        {"student_id": user["user_id"], "state": "NOT_STARTED"},
        {"$set": {
            "state":      "DEVICE_VERIFIED",
            "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
        }},
        upsert=False
    )

    send_log(MODULE_NAME, "INFO", user["user_id"], "",
             "device_verified", {"fingerprint": fingerprint[:16] + "..."})

    return success_response(
        data    = {
            "verified":    True,
            "user_id":     user["user_id"],
            "fingerprint": fingerprint[:16] + "..."
        },
        message = "Device verified. Exam access granted."
    )


# =============================================
# GET STUDENT DEVICE INFO (Teacher)
# GET /api/module03/student-device/<user_id>
# Role: teacher only
# =============================================

@app.route("/api/module03/student-device/<user_id>", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def get_student_device(user_id):
    db     = get_db()
    device = db["devices"].find_one({"user_id": user_id}, {"_id": 0})

    if not device:
        return error_response(404, "No device registered for this student")

    # Hide full fingerprint for privacy
    device["fingerprint_hash"] = device["fingerprint_hash"][:16] + "..."

    return success_response(
        data    = device,
        message = "Device info retrieved"
    )


# =============================================
# GET ALL DEVICE ALERTS (Teacher)
# GET /api/module03/alerts
# Role: teacher only
# =============================================

@app.route("/api/module03/alerts", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def get_alerts():
    db     = get_db()
    alerts = list(db["device_alerts"].find(
        {"resolved": False},
        {"_id": 0}
    ).sort("timestamp", -1).limit(50))

    return success_response(
        data    = {
            "total_alerts": len(alerts),
            "alerts":       alerts
        },
        message = "Device alerts retrieved"
    )


# =============================================
# RESOLVE ALERT (Teacher)
# POST /api/module03/resolve-alert
# Role: teacher only
# =============================================

@app.route("/api/module03/resolve-alert", methods=["POST"])
@jwt_required
@role_required(["teacher"])
def resolve_alert():
    data = request.get_json()

    if not data or "user_id" not in data:
        return error_response(400, "user_id required")

    db     = get_db()
    result = db["device_alerts"].update_many(
        {"user_id": data["user_id"], "resolved": False},
        {"$set": {
            "resolved":    True,
            "resolved_by": request.user_payload["user_id"],
            "resolved_at": datetime.datetime.utcnow().isoformat() + "Z",
            "note":        data.get("note", "")
        }}
    )

    send_log(MODULE_NAME, "INFO",
             request.user_payload["user_id"], "",
             "device_alert_resolved",
             {"student_id": data["user_id"]})

    return success_response(
        data    = {"resolved_count": result.modified_count},
        message = "Alert resolved"
    )


# =============================================
# RESET DEVICE (Teacher — e.g. student changed laptop)
# POST /api/module03/reset-device
# Role: teacher only
# =============================================

@app.route("/api/module03/reset-device", methods=["POST"])
@jwt_required
@role_required(["teacher"])
def reset_device():
    data = request.get_json()

    if not data or "user_id" not in data:
        return error_response(400, "user_id required")

    db = get_db()
    db["devices"].delete_one({"user_id": data["user_id"]})

    send_log(MODULE_NAME, "INFO",
             request.user_payload["user_id"], "",
             "device_reset",
             {
                 "student_id": data["user_id"],
                 "reason":     data.get("reason", "teacher reset")
             })

    return success_response(
        data    = {"user_id": data["user_id"]},
        message = "Device registration cleared. Student can register new device."
    )


# =============================================
# RISK DATA — For Module 17
# GET /api/module03/risk-data?user_id=X&exam_id=Y
# =============================================

@app.route("/api/module03/risk-data", methods=["GET"])
@jwt_required
def risk_data():
    user_id = request.args.get("user_id")
    exam_id = request.args.get("exam_id")

    if not user_id or not exam_id:
        return error_response(400, "user_id and exam_id are required")

    db     = get_db()
    alerts = db["device_alerts"].count_documents({
        "user_id":  user_id,
        "resolved": False
    })

    return success_response(
        data = {
            "module": MODULE_NAME,
            "data": [{
                "user_id":   user_id,
                "exam_id":   exam_id,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "metric":    "device_mismatch_count",
                "value":     alerts
            }]
        },
        message = "Risk data retrieved"
    )


if __name__ == "__main__":
    print(f"🔐 Module 03 — Device Fingerprinting running on port {PORT}")
    print(f"   POST /api/module03/register-device   (student)")
    print(f"   POST /api/module03/verify-device     (student)")
    print(f"   GET  /api/module03/student-device/<user_id>  (teacher)")
    print(f"   GET  /api/module03/alerts            (teacher)")
    print(f"   POST /api/module03/resolve-alert     (teacher)")
    print(f"   POST /api/module03/reset-device      (teacher)")
    print(f"   GET  /api/module03/risk-data         (module 17)")
    print(f"   GET  /api/module03/health")
    app.run(port=PORT, debug=True)
