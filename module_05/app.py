# module_05/app.py
# MODULE 05: ROLE-BASED ACCESS CONTROL (RBAC)
# PORT: 5005

import sys, os, datetime
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
MODULE_NAME = "Module_05_RBAC"
PORT = 5005

ROLE_PERMISSIONS = {
    "student": [
        "view_own_profile", "attempt_exam", "submit_answers",
        "validate_activation_code", "view_own_risk_score",
        "view_exam_questions", "check_time_remaining"
    ],
    "teacher": [
        "view_all_students", "create_exam", "delete_exam",
        "add_questions", "edit_questions", "generate_activation_code",
        "approve_student", "view_activity_logs", "view_risk_dashboard",
        "view_all_risk_scores", "reset_device", "view_all_sessions"
    ]
}

def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, [])

@app.route("/api/module05/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

@app.route("/api/module05/check-permission", methods=["GET"])
@jwt_required
def check_permission():
    permission = request.args.get("permission")
    if not permission:
        return error_response(400, "permission parameter required")

    user = request.user_payload
    role = user["role"]
    allowed = has_permission(role, permission)

    if not allowed:
        send_log(MODULE_NAME, "SECURITY", user["user_id"], "", "permission_denied",
                 {"role": role, "permission": permission})
        return error_response(403, f"Role '{role}' does not have permission: '{permission}'")

    return success_response(
        data={"role": role, "permission": permission, "allowed": True},
        message="Permission granted"
    )

@app.route("/api/module05/user-role", methods=["GET"])
@jwt_required
def user_role():
    user = request.user_payload
    role = user["role"]
    return success_response(
        data={"user_id": user["user_id"], "role": role,
              "permissions": ROLE_PERMISSIONS.get(role, [])},
        message="Role retrieved"
    )

@app.route("/api/module05/all-permissions", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def all_permissions():
    return success_response(data={"roles": ROLE_PERMISSIONS}, message="All permissions retrieved")

if __name__ == "__main__":
    print(f"Module 05 — RBAC running on port {PORT}")
    app.run(port=PORT, debug=True)
