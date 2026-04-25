# shared/response_helper.py
# =============================================
# DO NOT MODIFY THIS FILE
# Standardized API response format
# =============================================

import datetime
from flask import jsonify


def success_response(data: dict = {}, message: str = "Success", status_code: int = 200):
    """Return a standard success response."""
    return jsonify({
        "status": "success",
        "data": data,
        "message": message
    }), status_code


def error_response(error_code: int, message: str):
    """Return a standard error response."""
    return jsonify({
        "status": "error",
        "error_code": error_code,
        "message": message,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }), error_code
