# module_09/app.py
# =============================================
# MODULE 09: INPUT VALIDATION
# SQL/NoSQL injection and XSS prevention
# PORT: 5009
# DATABASE: MongoDB
# =============================================


import os
from dotenv import load_dotenv
load_dotenv()

import sys
import os
import re
import unicodedata
import html

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

app = Flask(__name__)

MODULE_NAME = "Module_09_Input_Validation"
PORT = 5009

# =============================================
# HEALTH CHECK — MANDATORY, DO NOT REMOVE
# =============================================
@app.route("/api/module09/health", methods=["GET"])
def health():
    return jsonify({
        "module": MODULE_NAME,
        "status": "healthy",
        "dependencies": ["mongodb"],
        "version": "1.0.0"
    }), 200


# =============================================
# CONFIGURATION
# =============================================
MAX_INPUT_LENGTH = 5000

# =============================================
# VALIDATION RULES
# =============================================
VALIDATION_RULES = {
    "username": {
        "pattern": r"^[a-zA-Z0-9_]{3,20}$",
        "max_length": 20,
        "description": "3-20 chars, alphanumeric and underscore only"
    },
    "password": {
        "pattern": r"^.{6,50}$",
        "max_length": 50,
        "description": "6-50 characters"
    },
    "email": {
        "pattern": r"^[^@]+@[^@]+\.[^@]+$",
        "max_length": 254,
        "description": "Valid email format"
    },
    "text": {
        "pattern": r"^[a-zA-Z0-9\s.,!?@#%&()\-_\+\=]{1,500}$",
        "max_length": 500,
        "description": "1-500 chars, basic text with common punctuation"
    },
    "answer": {
        "pattern": r"^[\w\s.,!?@#%&()\-_\+\=\*\:\;\/\[\]\{\}]{1,1000}$",
        "max_length": 1000,
        "description": "1-1000 chars, exam answer format"
    },
    "object_id": {
        "pattern": r"^[a-fA-F0-9]{24}$",
        "max_length": 24,
        "description": "MongoDB ObjectId format"
    }
}

# =============================================
# MONGODB INJECTION PATTERNS
# =============================================
MONGODB_INJECTION_PATTERNS = [
    # MongoDB operators in JSON
    r'\{\s*"\$[a-zA-Z]+\s*":',
    r'\{\s*\$[a-zA-Z]+\s*:',
    
    # MongoDB operators as strings
    r'\$(?:eq|ne|gt|gte|lt|lte|in|nin|or|and|not|nor|exists|type|mod|regex|text|search|where|expr)\b',
    
    # Dangerous MongoDB methods
    r'db\.\w+\s*\(',
    r'\.findOne\s*\(',
    r'\.find\s*\(',
    r'\.aggregate\s*\(',
    r'\.mapReduce\s*\(',
    
    # MongoDB-specific injections
    r'\$where\s*:',
    r'\$regex\s*:',
    r'sleep\s*\(\s*\d+\s*\)',
    r'ObjectId\s*\(',
    r'ISODate\s*\(',
]

XSS_PATTERNS = [
    # Script injection
    r'<\s*script[^>]*>',
    r'<\s*/\s*script\s*>',
    
    # Event handlers
    r'on\w+\s*=\s*["\']',
    r'on\w+\s*=\s*\w+\s*\(',
    
    # Protocol handlers
    r'javascript\s*:',
    r'vbscript\s*:',
    r'data\s*:\s*text/html',
    
    # Dangerous functions
    r'eval\s*\(',
    r'alert\s*\(',
    r'document\.\w+',
    r'window\.\w+',
    
    # Other injection vectors
    r'<\s*iframe[^>]*>',
    r'<\s*embed[^>]*>',
    r'<\s*object[^>]*>',
    r'<\s*svg[^>]*>',
]

# Combine all attack patterns
ALL_ATTACK_PATTERNS = MONGODB_INJECTION_PATTERNS + XSS_PATTERNS


# =============================================
# INPUT PREPROCESSING
# =============================================
def normalize_unicode(value: str) -> str:
    """Normalize Unicode to prevent encoding bypass attacks"""
    if not value:
        return ""
    
    # NFKC normalization to handle full-width chars, superscripts, etc.
    value = unicodedata.normalize('NFKC', value)
    
    # Remove null bytes and control characters
    value = value.replace('\x00', '')
    value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    return value


# =============================================
# ATTACK DETECTION
# =============================================
def detect_attack(value: str):
    """Detect injection attacks in input value"""
    if not value:
        return False, None

    normalized = normalize_unicode(value)
    normalized_lower = normalized.lower()

    # Check all attack patterns
    for pattern in ALL_ATTACK_PATTERNS:
        match = re.search(pattern, normalized_lower, re.IGNORECASE)
        if match:
            # Determine attack type
            if pattern in MONGODB_INJECTION_PATTERNS:
                attack_type = "mongodb_injection"
            else:
                attack_type = "xss_injection"
            
            return True, {
                "attack_type": attack_type,
                "pattern_matched": pattern,
                "matched_text": match.group()[:50]
            }

    # Check for MongoDB specific dangers
    if isinstance(value, str):
        # Check for dot notation injection
        if re.match(r'^\w+\.\w+(\.\w+)*$', value) and len(value) < 100:
            return True, {
                "attack_type": "mongodb_dot_notation",
                "pattern_matched": "dot_notation",
                "matched_text": value[:50]
            }
        
        # Check for BSON type injection
        bson_patterns = [
            r'ObjectId\s*\(\s*["\']',
            r'new\s+Date\s*\(',
            r'NumberInt\s*\(',
            r'NumberLong\s*\(',
        ]
        for pattern in bson_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                return True, {
                    "attack_type": "bson_type_injection",
                    "pattern_matched": pattern,
                    "matched_text": value[:50]
                }

    return False, None


# =============================================
# FIELD VALIDATION
# =============================================
def validate_field(field: str, value: str):
    """Validate field against defined rules"""
    rule = VALIDATION_RULES.get(field)

    if not rule:
        return False, f"Unknown field type: {field}"

    # Check length
    if len(value) > rule.get('max_length', MAX_INPUT_LENGTH):
        return False, f"Field exceeds maximum length of {rule['max_length']}"

    # Check pattern
    pattern = rule.get('pattern')
    if pattern and not re.match(pattern, value):
        return False, f"Invalid format. Expected: {rule['description']}"

    return True, None


# =============================================
# SANITIZATION
# =============================================
def sanitize_value(value: str) -> str:
    """Sanitize input for safe storage in MongoDB"""
    if not value:
        return ""

    # Step 1: Normalize unicode
    clean = normalize_unicode(value)

    # Step 2: Remove HTML tags and scripts
    # Simple tag removal (more reliable than BeautifulSoup for security)
    clean = re.sub(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', '', clean, flags=re.IGNORECASE | re.DOTALL)
    clean = re.sub(r'<[^>]*>', '', clean)
    
    # Step 3: Decode HTML entities to prevent bypass
    clean = html.unescape(clean)
    
    # Step 4: Remove MongoDB operators from string content
    clean = re.sub(r'\$\b(?:where|regex|options|set|inc|push|pull|addToSet|each|slice|sort|elemMatch)\b', 
               '', clean, flags=re.IGNORECASE)

    # Step 5: Remove dangerous characters
    # Keep only safe characters
    clean = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', clean)
    
    # Step 6: Normalize whitespace
    clean = re.sub(r'\s+', ' ', clean)
    
    # Step 7: Trim
    clean = clean.strip()

    return clean

# =============================================
# ENDPOINT 1 - VALIDATE INPUT
# =============================================
@app.route("/api/module09/validate-input", methods=["POST"])
@jwt_required
def validate_input_endpoint():
    """
    Validate and sanitize user input
    Detects MongoDB injection and XSS attacks
    """
    user = request.user_payload
    data = request.get_json(silent=True) or {}

    field = data.get("field", "")
    value = str(data.get("value", ""))
    exam_id = data.get("exam_id", "")

    # Step 1: Check input length
    if len(value) > MAX_INPUT_LENGTH:
        return error_response(
            message=f"Input exceeds maximum length of {MAX_INPUT_LENGTH} characters",
            error_code=400
        )

    # Step 2: Detect attacks
    is_attack, attack_details = detect_attack(value)

    if is_attack:
        send_log(
            module_name=MODULE_NAME,
            level="SECURITY",
            user_id=user.get("user_id", "unknown"),
            exam_id=exam_id,
            action="injection_attack_detected",
            details={
                "field": field,
                "attack_type": attack_details["attack_type"],
                "pattern": attack_details["pattern_matched"],
                "matched_text": attack_details["matched_text"],
                "ip": request.remote_addr
            }
        )

        return error_response(
            message="Malicious input detected and blocked",
            error_code=400
        )

    # Step 3: Validate field format
    is_valid, error_msg = validate_field(field, value)

    if not is_valid:
        return error_response(
            message=error_msg,
            error_code=400
        )

    # Step 4: Sanitize value
    clean_value = sanitize_value(value)

    # Step 5: Build safe MongoDB query
    # safe_query = build_safe_query(field, clean_value)

    # Step 6: Log success
    try:
        send_log(
            module_name=MODULE_NAME,
            level="INFO",
            user_id=user.get("user_id", "unknown"),
            exam_id=exam_id,
            action="input_validated",
            details={
                "field": field,
                "rule": VALIDATION_RULES.get(field, {}).get('description', 'general'),
                "original_length": len(value),
                "sanitized_length": len(clean_value)
            }
        )
    except Exception:
        pass

    return success_response(
        data={
            "field": field,
            "is_valid": True,
            "sanitized_value": clean_value,
            # "safe_query": safe_query
        },
        message="Input validated and sanitized successfully"
    )


# =============================================
# ENDPOINT 2 - SANITIZE ONLY
# =============================================
@app.route("/api/module09/sanitize", methods=["POST"])
@jwt_required
def sanitize_endpoint():
    """
    Sanitize input without validation
    Useful for free-form text that needs cleaning
    """
    user = request.user_payload
    data = request.get_json(silent=True) or {}

    value = str(data.get("value", ""))
    exam_id = data.get("exam_id", "")

    # Check input length
    if len(value) > MAX_INPUT_LENGTH:
        return error_response(
            message=f"Input exceeds maximum length of {MAX_INPUT_LENGTH} characters",
            error_code=400
        )

    # Check for attacks (log only, don't block)
    is_attack, attack_details = detect_attack(value)
    
    # Sanitize the value
    clean_value = sanitize_value(value)

    # Log if attack was detected
    if is_attack:
        try:
            send_log(
                module_name=MODULE_NAME,
                level="SECURITY",
                user_id=user.get("user_id", "unknown"),
                exam_id=exam_id,
                action="sanitized_suspicious_input",
                details={
                    "attack_type": attack_details["attack_type"],
                    "pattern": attack_details["pattern_matched"],
                    "ip": request.remote_addr
                }
            )
        except Exception:
            pass
    else:
        try:
            send_log(
                module_name=MODULE_NAME,
                level="INFO",
                user_id=user.get("user_id", "unknown"),
                exam_id=exam_id,
                action="input_sanitized",
                details={
                    "original_length": len(value),
                    "sanitized_length": len(clean_value)
                }
            )
        except Exception:
            pass

    return success_response(
        data={
            "sanitized_value": clean_value,
            "suspicious_input_detected": is_attack,
            "original_length": len(value),
            "sanitized_length": len(clean_value)
        },
        message="Input sanitized successfully"
    )


# =============================================
# MAIN
# =============================================
if __name__ == "__main__":
    print(f"🔐 Module 09 — Secure Input Validation for MongoDB running on port {PORT}")
    app.run(port=PORT, debug=True)