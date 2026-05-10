# module_09/app.py
# MODULE 09: INPUT VALIDATION — Injection Prevention
# PORT: 5009

import sys, os, datetime, re
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from shared.jwt_helper import jwt_required
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

app = Flask(__name__)
MODULE_NAME = "Module_09_InputValidation"
PORT = 5009

# Dangerous patterns
NOSQL_PATTERNS = [r'\$where', r'\$gt', r'\$lt', r'\$ne', r'\$in', r'\$nin', r'\$exists', r'\$regex']
XSS_PATTERNS   = [r'<script', r'javascript:', r'onerror=', r'onload=', r'<iframe', r'alert\(']
SQL_PATTERNS   = [r"'.*--", r';\s*drop\s', r';\s*delete\s', r'union\s+select', r'1=1', r"' or '"]

def check_input(value: str) -> dict:
    """Check a string for injection attacks. Returns {safe, threats}."""
    if not isinstance(value, str):
        return {"safe": True, "threats": []}

    val_lower = value.lower()
    threats = []

    for p in NOSQL_PATTERNS:
        if re.search(p, val_lower):
            threats.append({"type": "nosql_injection", "pattern": p})
    for p in XSS_PATTERNS:
        if re.search(p, val_lower):
            threats.append({"type": "xss", "pattern": p})
    for p in SQL_PATTERNS:
        if re.search(p, val_lower):
            threats.append({"type": "sql_injection", "pattern": p})

    return {"safe": len(threats) == 0, "threats": threats}

def sanitize(value: str) -> str:
    """Basic sanitization — remove dangerous chars."""
    if not isinstance(value, str):
        return str(value)
    value = re.sub(r'<[^>]+>', '', value)          # strip HTML tags
    value = re.sub(r'[;\$\{\}]', '', value)         # remove ; $ { }
    value = value.replace("'", "''").strip()         # escape single quotes
    return value[:5000]                              # cap length

@app.route("/api/module09/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": [], "version": "1.0.0"}, 200

@app.route("/api/module09/validate-input", methods=["POST"])
@jwt_required
def validate_input():
    """Check all string fields in input for injection attacks."""
    data = request.get_json()
    if not data:
        return error_response(400, "No input provided")

    user    = request.user_payload
    results = {}
    threats_found = []

    def check_recursive(obj, path=""):
        if isinstance(obj, str):
            result = check_input(obj)
            results[path] = result
            if not result["safe"]:
                threats_found.extend([{**t, "field": path} for t in result["threats"]])
        elif isinstance(obj, dict):
            for k, v in obj.items():
                check_recursive(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                check_recursive(v, f"{path}[{i}]")

    check_recursive(data)

    if threats_found:
        send_log(MODULE_NAME, "SECURITY", user["user_id"], "",
                 "injection_attempt_detected",
                 {"threats": threats_found, "input_keys": list(data.keys())})
        return error_response(400, f"Malicious input detected: {threats_found[0]['type']}")

    return success_response(
        data={"safe": True, "fields_checked": len(results)},
        message="Input is safe"
    )

@app.route("/api/module09/sanitize", methods=["POST"])
@jwt_required
def sanitize_input():
    """Sanitize all string fields in input."""
    data = request.get_json()
    if not data:
        return error_response(400, "No input provided")

    def sanitize_recursive(obj):
        if isinstance(obj, str):
            return sanitize(obj)
        elif isinstance(obj, dict):
            return {k: sanitize_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_recursive(v) for v in obj]
        return obj

    sanitized = sanitize_recursive(data)
    return success_response(data={"sanitized": sanitized}, message="Input sanitized")

if __name__ == "__main__":
    print(f"Module 09 — Input Validation running on port {PORT}")
    app.run(port=PORT, debug=True)
