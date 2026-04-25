# module_16/app.py
# =============================================
# MODULE 16: ANSWER SIMILARITY DETECTION
# TF-IDF + Cosine similarity to detect copying
# PORT: 5016
# =============================================

import sys
import os
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

app = Flask(__name__)

MODULE_NAME = "Module_16_Answer_Similarity"
PORT        = 5016

# =============================================
# HEALTH CHECK — MANDATORY, DO NOT REMOVE
# =============================================
@app.route("/api/module16/health", methods=["GET"])
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
# POST /api/module16/check-similarity
# GET  /api/module16/risk-data
# =============================================

# EXAMPLE endpoint — replace with your actual implementation
@app.route("/api/module16/example", methods=["POST"])
@jwt_required
def example_endpoint():
    """
    Replace this with your actual endpoint.
    request.user_payload contains JWT data: user_id, role, etc.
    """
    user = request.user_payload
    db   = get_db()

    # Log the action
    send_log(
        module_name = MODULE_NAME,
        level       = "INFO",
        user_id     = user["user_id"],
        exam_id     = request.json.get("exam_id", ""),
        action      = "example_action",
        details     = {"request_data": request.json}
    )

    # Your logic here
    result = {}

    return success_response(data=result, message="Action completed")


if __name__ == "__main__":
    print(f"🔐 Module 16 — Answer Similarity Detection running on port {PORT}")
    app.run(port=PORT, debug=True)
