# module_01/app.py
# =============================================
# MODULE 01: SECURE AUTHENTICATION
# bcrypt password hashing + JWT issuance + OTP MFA
# PORT: 5001
# =============================================

import sys
import os
import datetime
import html
import random
import re
import smtplib
import string
from email.message import EmailMessage
from dotenv import load_dotenv
import requests

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import jwt
import bcrypt
from flask import Flask, request, jsonify
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response
from shared.jwt_helper import jwt_required, role_required, JWT_SECRET, JWT_ALGORITHM

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

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str:
    return str(value or "").strip().lower()


def email_otp_configured() -> bool:
    from_email = os.getenv("SMTP_FROM_EMAIL")
    return bool(
        from_email
        and (
            os.getenv("BREVO_API_KEY")
            or os.getenv("SMTP_HOST")
        )
    )


def generate_otp() -> str:
    demo_otp = os.getenv("DEMO_OTP", "").strip()
    if demo_otp.isdigit() and len(demo_otp) == 6:
        return demo_otp
    return "".join(random.choices(string.digits, k=6))


def send_otp_email(to_email: str, otp: str) -> bool:
    """Send OTP using Brevo API when available, otherwise SMTP."""
    if not email_otp_configured():
        return False

    from_email = os.getenv("SMTP_FROM_EMAIL")
    subject = "Secure Exam System OTP"
    text_content = (
        f"Your Secure Exam System OTP is {otp}. "
        "It expires in 5 minutes. Do not share it with anyone."
    )
    escaped_otp = html.escape(otp)
    html_content = f"""
        <html>
          <body>
            <p>Your Secure Exam System OTP is:</p>
            <h2>{escaped_otp}</h2>
            <p>This code expires in 5 minutes. Do not share it with anyone.</p>
          </body>
        </html>
        """

    api_key = os.getenv("BREVO_API_KEY", "").strip()
    if api_key:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "sender": {
                    "email": from_email,
                    "name": "Secure Exam System",
                },
                "to": [{"email": to_email}],
                "subject": subject,
                "textContent": text_content,
                "htmlContent": html_content,
            },
            timeout=10,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Brevo API email failed: HTTP {response.status_code} "
                f"{response.text[:300]}"
            )
        return True

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() != "false"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(text_content)
    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(host, port, timeout=10) as server:
        if use_tls:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(msg)
    return True

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

    required = ["email", "password", "role"]
    for field in required:
        if not data or field not in data:
            return error_response(400, f"Missing field: {field}")

    if data["role"] not in ["student", "teacher"]:
        return error_response(400, "Role must be 'student' or 'teacher'")
    email = normalize_email(data["email"])
    if not EMAIL_RE.fullmatch(email):
        return error_response(400, "Valid email address is required")
    password = str(data["password"])
    if (
        len(password) < 8
        or not re.search(r"[A-Za-z]", password)
        or not re.search(r"\d", password)
    ):
        return error_response(
            400,
            "Password must be at least 8 characters and include a letter and number"
        )

    db    = get_db()
    users = db["users"]

    # Check duplicate before role provisioning so duplicate registration remains 409.
    if users.find_one({"email": email}):
        return error_response(409, "Email already exists")

    if data["role"] == "teacher" and users.find_one({"role": "teacher"}):
        registration_code = os.getenv("TEACHER_REGISTRATION_CODE", "")
        if (
            not registration_code
            or data.get("teacher_registration_code") != registration_code
        ):
            return error_response(
                403,
                "Teacher registration requires an administrator invitation code"
            )

    # Hash password with bcrypt
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user = {
        "username":          email,
        "email":             email,
        "password_hash":     hashed.decode("utf-8"),
        "role":              data["role"],
        "created_at":        datetime.datetime.utcnow().isoformat(),
        "is_active":         True,
        "is_verified":       False,
        "device_fingerprint_hash": ""
    }

    result  = users.insert_one(user)
    user_id = str(result.inserted_id)
    otp = generate_otp()
    otp_store[user_id] = {
        "otp": otp,
        "purpose": "registration",
        "expires_at": (
            datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        ).isoformat()
    }

    email_sent = False
    if email_otp_configured():
        try:
            email_sent = send_otp_email(email, otp)
        except Exception as exc:
            otp_store.pop(user_id, None)
            users.delete_one({"_id": result.inserted_id})
            send_log(MODULE_NAME, "ERROR", user_id, "", "registration_otp_email_failed",
                     {"email": email, "error": str(exc)})
            return error_response(503, "Unable to send verification email. Please try again later.")

    if not email_sent:
        print(f"[DEV OTP] Registration email: {email} | OTP: {otp}")

    send_log(MODULE_NAME, "INFO", user_id, "", "user_registered",
             {"email": email, "role": data["role"], "verification_email_sent": email_sent})

    return success_response(
        data = {
            "user_id": user_id,
            "email": email,
            "username": email,
            "role": data["role"],
            "verification_required": True,
            "email_sent": email_sent,
            "message": (
                "OTP sent to your registered email."
                if email_sent
                else "Use the configured demo OTP or server log OTP."
            ),
        },
        message = (
            "Registration successful. OTP sent to your email."
            if email_sent
            else "Registration successful. Use the configured demo OTP or server log OTP."
        )
    )


# =============================================
# LOGIN
# POST /api/module01/login
# =============================================
@app.route("/api/module01/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or "password" not in data or ("email" not in data and "username" not in data):
        return error_response(400, "Email and password required")

    db    = get_db()
    users = db["users"]
    login_identifier = normalize_email(data.get("email") or data.get("username"))
    user = users.find_one({"email": login_identifier})
    if not user:
        # Backward compatibility for pre-email demo accounts such as demo_teacher.
        user = users.find_one({"username": login_identifier})

    if not user:
        send_log(MODULE_NAME, "SECURITY", "", "", "login_failed_user_not_found",
                 {"email": login_identifier})
        return error_response(401, "Invalid credentials")

    # Verify bcrypt password
    password_valid = bcrypt.checkpw(
        data["password"].encode("utf-8"),
        user["password_hash"].encode("utf-8")
    )

    if not password_valid:
        send_log(MODULE_NAME, "SECURITY", str(user["_id"]), "", "login_failed_wrong_password",
                 {"email": user.get("email", user.get("username", ""))})
        return error_response(401, "Invalid credentials")

    # Generate OTP for MFA
    otp = generate_otp()
    otp_store[str(user["_id"])] = {
        "otp":        otp,
        "purpose":    "login",
        "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat()
    }

    target_email = user.get("email", "")
    email_sent = False
    if target_email and email_otp_configured():
        try:
            email_sent = send_otp_email(target_email, otp)
        except Exception as exc:
            del otp_store[str(user["_id"])]
            send_log(MODULE_NAME, "ERROR", str(user["_id"]), "", "otp_email_failed",
                     {"email": target_email, "error": str(exc)})
            return error_response(503, "Unable to send OTP email. Please try again later.")

    send_log(MODULE_NAME, "INFO", str(user["_id"]), "", "login_otp_sent",
             {"email": target_email or user.get("username", ""), "email_sent": email_sent})

    if not email_sent:
        print(f"[DEV OTP] User: {user.get('email', user.get('username'))} | OTP: {otp}")

    return success_response(
        data    = {
            "user_id":  str(user["_id"]),
            "email": target_email,
            "email_sent": email_sent,
            "message":  "OTP sent to registered email." if email_sent else "OTP generated. Check server logs or configured demo OTP."
        },
        message = "OTP sent. Verify to complete login."
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

    if not user.get("is_verified", True):
        db["users"].update_one(
            {"_id": user["_id"]},
            {"$set": {
                "is_verified": True,
                "verified_at": datetime.datetime.utcnow().isoformat() + "Z"
            }}
        )
        user["is_verified"] = True

    # Generate session ID
    session_id = "".join(random.choices(string.ascii_letters + string.digits, k=32))

    # Issue JWT — THIS IS THE ONLY PLACE JWT IS ISSUED
    payload = {
        "user_id":                 str(user["_id"]),
        "username":                user["username"],
        "email":                   user.get("email", user.get("username", "")),
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
            "email":    user.get("email", user.get("username", "")),
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
@role_required(["teacher"])
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
