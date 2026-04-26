# module_09/app.py
# =============================================
# MODULE 09: INPUT VALIDATION
# SQL/NoSQL injection and XSS prevention
# PORT: 5009
# =============================================

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

app = Flask(__name__)

MODULE_NAME = "Module_09_Input_Validation"
PORT        = 5009

# =============================================
# HEALTH CHECK — MANDATORY, DO NOT REMOVE
# =============================================
@app.route("/api/module09/health", methods=["GET"])
def health():
    return jsonify({
        "module":       MODULE_NAME,
        "status":       "healthy",
        "dependencies": ["mongodb"],
        "version":      "1.0.0"
    }), 200


# =============================================
# YOUR MODULE ENDPOINTS GO BELOW
# Available endpoints to implement:
# POST /api/module09/validate-input
# POST /api/module09/sanitize
# =============================================

import sys
import os
import re
from bs4 import BeautifulSoup

# =============================================
# VALIDATION RULES
# =============================================
VALIDATION_RULES = {
    "username": r"^[a-zA-Z0-9_]{3,20}$",
    "password": r"^.{6,50}$",
    "email": r"^[^@]+@[^@]+\.[^@]+$",
    "text": r"^[a-zA-Z0-9\s.,!?@#%&()\-]{1,500}$"
}

# =============================================
# STRONG ATTACK DETECTION (FIXED)
# =============================================
ATTACK_PATTERNS = [
    r"\$ne", r"\$gt", r"\$lt", r"\$regex", r"\$where",
    r"<script.*?>", r"</script>",
    r"javascript:", r"onerror=", r"onload=",
    r"union\s+select", r"drop\s+table"
]


def detect_attack(value: str):
    if not value:
        return False, None

    value_lower = value.lower()

    for pattern in ATTACK_PATTERNS:
        if re.search(pattern, value_lower, re.IGNORECASE):
            return True, pattern

    return False, None


# =============================================
# FIELD VALIDATION
# =============================================
def validate_input_field(field, value):
    pattern = VALIDATION_RULES.get(field)

    if not pattern:
        return False, "Unknown field type"

    if not re.match(pattern, value):
        return False, "Invalid format"

    return True, None


# =============================================
# SECURE SANITIZER (FIXED PROPERLY)
# =============================================
def sanitize_value(value: str):
    if not value:
        return ""

    # 1. Detect obvious script injection BEFORE cleaning
    if re.search(r"(?i)<\s*script", value):
        value = re.sub(r"(?i)<\s*/?\s*script\s*>", "", value)

    # 2. Remove HTML tags safely
    clean = BeautifulSoup(value, "html.parser").get_text()

    # 3. Remove only dangerous injection characters (safe minimal set)
    clean = re.sub(r"[\$\{\}<>/;:'\"\\]", "", clean)

    # 4. Normalize spaces
    clean = re.sub(r"\s+", " ", clean)

    return clean.strip()


# =============================================
# ENDPOINT 1 - VALIDATE INPUT
# =============================================
@app.route("/api/module09/validate-input", methods=["POST"])
@jwt_required
def validate_input_endpoint():

    user = request.user_payload
    data = request.json or {}

    field = data.get("field", "")
    value = str(data.get("value", ""))
    exam_id = data.get("exam_id", "")

    # 🔴 Attack detection
    is_attack, pattern = detect_attack(value)

    if is_attack:
        send_log(
            module_name=MODULE_NAME,
            level="SECURITY",
            user_id=user["user_id"],
            exam_id=exam_id,
            action="injection_detected",
            details={"input": value, "pattern": pattern}
        )

        return error_response(
            message="Malicious input detected",
            error_code=400
        )

    # 🔐 Field validation
    is_valid, error_msg = validate_input_field(field, value)

    if not is_valid:
        return error_response(
            message=error_msg,
            error_code=400
        )

    # 🧼 Sanitize
    clean_value = sanitize_value(value)

    # 📝 Log success (safe fallback)
    try:
        send_log(
            module_name=MODULE_NAME,
            level="INFO",
            user_id=user["user_id"],
            exam_id=exam_id,
            action="input_validated",
            details={"field": field}
        )
    except:
        pass

    return success_response(
        data={
            "is_valid": True,
            "sanitized_value": clean_value
        },
        message="Input validated successfully"
    )


# =============================================
# ENDPOINT 2 - SANITIZE ONLY
# =============================================
@app.route("/api/module09/sanitize", methods=["POST"])
@jwt_required
def sanitize_endpoint():

    user = request.user_payload
    data = request.json or {}

    value = str(data.get("value", ""))
    exam_id = data.get("exam_id", "")

    clean_value = sanitize_value(value)

    try:
        send_log(
            module_name=MODULE_NAME,
            level="INFO",
            user_id=user["user_id"],
            exam_id=exam_id,
            action="input_sanitized",
            details={"original": value}
        )
    except:
        pass

    return success_response(
        data={
            "sanitized_value": clean_value
        },
        message="Input sanitized successfully"
    )


# =============================================
# MAIN
# =============================================
if __name__ == "__main__":
    print(f"🔐 Module 09 — Secure Input Validation running on port {PORT}")
    app.run(port=PORT, debug=True)