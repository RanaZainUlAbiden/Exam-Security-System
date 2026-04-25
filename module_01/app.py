# module_01/app.py
# =============================================
# MODULE 01: SECURE AUTHENTICATION
# bcrypt password hashing + JWT issuance + OTP MFA
# PORT: 5001
# =============================================

import sys
import os
import datetime
import random
import string

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import jwt
import bcrypt
from flask import Flask, request, jsonify
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response
from shared.jwt_helper import jwt_required, JWT_SECRET, JWT_ALGORITHM

app = Flask(__name__)

MODULE_NAME = "Module_01_Auth"
PORT        = 5001

# In-memory OTP store {user_id: {otp, expires_at}}
otp_store = {}

# Exam state store {exam_id: state}
exam_states = {}

VALID_STATES = [
    "NOT_STARTED", "DEVICE_VERIFIED", "TEACHER_APPROVED",
    "ACTIVATION_VALID", "IN_PROGRESS", "SUBMITTED",
    "ANALYZING", "COMPLETED"
]

# =============================================
# HEALTH CHECK
# =============================================
@app.route("/api/module01/health", methods=["GET"])
def health():
    return jsonify({
        "module":       MODULE_NAME,
        "status":       "healthy",
        "dependencies": ["mongodb"],
        "version":      "1.0.0"
    }), 200


# =============================================
# REGISTER
# POST /api/module01/register
# =============================================
@app.route("/api/module01/register", methods=["POST"])
def register():
    data = request.get_json()

    required = ["username", "password", "role"]
    for field in required:
        if not data or field not in data:
            return error_response(400, f"Missing field: {field}")

    if data["role"] not in ["student", "teacher"]:
        return error_response(400, "Role must be 'student' or 'teacher'")

    db    = get_db()
    users = db["users"]

    # Check duplicate
    if users.find_one({"username": data["username"]}):
        return error_response(409, "Username already exists")

    # Hash password with bcrypt
    hashed = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt())

    user = {
        "username":          data["username"],
        "password_hash":     hashed.decode("utf-8"),
        "role":              data["role"],
        "created_at":        datetime.datetime.utcnow().isoformat(),
        "is_active":         True,
        "device_fingerprint_hash": ""
    }

    result  = users.insert_one(user)
    user_id = str(result.inserted_id)

    send_log(MODULE_NAME, "INFO", user_id, "", "user_registered",
             {"username": data["username"], "role": data["role"]})

    return success_response(
        data    = {"user_id": user_id, "username": data["username"], "role": data["role"]},
        message = "User registered successfully"
    )


# =============================================
# LOGIN
# POST /api/module01/login
# =============================================
@app.route("/api/module01/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or "username" not in data or "password" not in data:
        return error_response(400, "Username and password required")

    db    = get_db()
    users = db["users"]
    user  = users.find_one({"username": data["username"]})

    if not user:
        send_log(MODULE_NAME, "SECURITY", "", "", "login_failed_user_not_found",
                 {"username": data["username"]})
        return error_response(401, "Invalid credentials")

    # Verify bcrypt password
    password_valid = bcrypt.checkpw(
        data["password"].encode("utf-8"),
        user["password_hash"].encode("utf-8")
    )

    if not password_valid:
        send_log(MODULE_NAME, "SECURITY", str(user["_id"]), "", "login_failed_wrong_password",
                 {"username": data["username"]})
        return error_response(401, "Invalid credentials")

    # Generate OTP for MFA
    otp = "".join(random.choices(string.digits, k=6))
    otp_store[str(user["_id"])] = {
        "otp":        otp,
        "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat()
    }

    send_log(MODULE_NAME, "INFO", str(user["_id"]), "", "login_otp_sent",
             {"username": data["username"]})

    # In real system: send OTP via email/SMS
    # For dev/testing: return OTP in response
    return success_response(
        data    = {
            "user_id":  str(user["_id"]),
            "otp":      otp,   # REMOVE THIS IN PRODUCTION
            "message":  "OTP sent. Use /verify-otp to get JWT token."
        },
        message = "OTP generated. Verify to complete login."
    )


# =============================================
# VERIFY OTP → ISSUE JWT
# POST /api/module01/verify-otp
# =============================================
@app.route("/api/module01/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()

    if not data or "user_id" not in data or "otp" not in data:
        return error_response(400, "user_id and otp required")

    user_id    = data["user_id"]
    stored_otp = otp_store.get(user_id)

    if not stored_otp:
        return error_response(401, "No OTP found. Please login again.")

    # Check OTP expiry
    expires_at = datetime.datetime.fromisoformat(stored_otp["expires_at"])
    if datetime.datetime.utcnow() > expires_at:
        del otp_store[user_id]
        return error_response(401, "OTP expired. Please login again.")

    # Check OTP value
    if stored_otp["otp"] != data["otp"]:
        send_log(MODULE_NAME, "SECURITY", user_id, "", "otp_verification_failed", {})
        return error_response(401, "Invalid OTP")

    # OTP valid — clear it
    del otp_store[user_id]

    # Get user from DB
    from bson import ObjectId
    db   = get_db()
    user = db["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        return error_response(404, "User not found")

    # Generate session ID
    session_id = "".join(random.choices(string.ascii_letters + string.digits, k=32))

    # Issue JWT — THIS IS THE ONLY PLACE JWT IS ISSUED
    payload = {
        "user_id":                 str(user["_id"]),
        "username":                user["username"],
        "role":                    user["role"],
        "session_id":              session_id,
        "device_fingerprint_hash": user.get("device_fingerprint_hash", ""),
        "exp":                     datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    send_log(MODULE_NAME, "INFO", user_id, "", "jwt_issued",
             {"username": user["username"], "role": user["role"]})

    return success_response(
        data    = {
            "token":    token,
            "user_id":  str(user["_id"]),
            "username": user["username"],
            "role":     user["role"],
            "expires_in": "3 hours"
        },
        message = "Login successful. JWT issued."
    )


# =============================================
# EXAM STATE — Used by all modules
# GET /api/module01/exam-state/<exam_id>
# =============================================
@app.route("/api/exam/state/<exam_id>", methods=["GET"])
@jwt_required
def get_exam_state(exam_id):
    db   = get_db()
    exam = db["exams"].find_one({"exam_id": exam_id})

    if not exam:
        # Default state for new exams
        return success_response(
            data    = {"exam_id": exam_id, "state": "NOT_STARTED"},
            message = "Exam state retrieved"
        )

    return success_response(
        data    = {"exam_id": exam_id, "state": exam.get("state", "NOT_STARTED")},
        message = "Exam state retrieved"
    )


@app.route("/api/exam/state/<exam_id>", methods=["POST"])
@jwt_required
def update_exam_state(exam_id):
    data = request.get_json()

    if "state" not in data or data["state"] not in VALID_STATES:
        return error_response(400, f"Invalid state. Must be one of: {VALID_STATES}")

    db = get_db()
    db["exams"].update_one(
        {"exam_id": exam_id},
        {"$set": {"state": data["state"], "updated_at": datetime.datetime.utcnow().isoformat()}},
        upsert=True
    )

    send_log(MODULE_NAME, "INFO", request.user_payload["user_id"], exam_id,
             "exam_state_updated", {"new_state": data["state"]})

    return success_response(
        data    = {"exam_id": exam_id, "state": data["state"]},
        message = "Exam state updated"
    )


if __name__ == "__main__":
    print(f"🔐 Module 01 — Secure Authentication running on port {PORT}")
    print(f"   POST /api/module01/register")
    print(f"   POST /api/module01/login")
    print(f"   POST /api/module01/verify-otp")
    print(f"   GET  /api/exam/state/<exam_id>")
    app.run(port=PORT, debug=True)
