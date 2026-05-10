# shared/jwt_helper.py
# =============================================
# DO NOT MODIFY THIS FILE
# Used by all modules for JWT validation
# =============================================

import jwt
import datetime
from functools import wraps
from flask import request, jsonify

import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "exam_security_UET_2024_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def validate_token(token: str):
    """
    Validates a JWT token.
    Returns payload dict if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def jwt_required(f):
    """
    Decorator to protect Flask routes with JWT validation.
    Usage: @jwt_required above your route function.
    Injects request.user_payload with JWT data.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "status": "error",
                "error_code": 401,
                "message": "Missing or malformed Authorization header",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }), 401

        token = auth_header.split(" ")[1]
        payload = validate_token(token)

        if payload is None:
            return jsonify({
                "status": "error",
                "error_code": 401,
                "message": "JWT expired or invalid",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }), 401

        request.user_payload = payload
        return f(*args, **kwargs)

    return decorated


def role_required(allowed_roles: list):
    """
    Decorator to enforce role-based access.
    Use AFTER @jwt_required.
    Usage: @role_required(["teacher"])
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(request, 'user_payload', None)
            if not user or user.get("role") not in allowed_roles:
                return jsonify({
                    "status": "error",
                    "error_code": 403,
                    "message": f"Access denied. Required roles: {allowed_roles}",
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
