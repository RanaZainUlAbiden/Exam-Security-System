# Module 5 - RBAC

import sys
import os
from flask import Flask, request, jsonify
from bson.objectid import ObjectId

# Import shared utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.db_config import get_db, COLLECTIONS
from shared.jwt_helper import jwt_required
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

app = Flask(__name__)

MODULE_NAME = "Module_05_RBAC"
PORT = 5005

PERMISSIONS = {
    "student": [
        "view_own_profile", 
        "attempt_exam", 
        "submit_answers", 
        "validate_activation_code", 
        "view_own_risk_score"
    ],
    "teacher": [
        "view_all_students", 
        "create_exam", 
        "delete_exam", 
        "add_questions", 
        "edit_questions", 
        "generate_activation_code", 
        "approve_student", 
        "view_activity_logs", 
        "view_risk_dashboard", 
        "view_all_risk_scores"
    ]
}

@app.route("/api/module05/health", methods=["GET"])
def health():
    return jsonify({
        "module": MODULE_NAME,
        "status": "healthy",
        "dependencies": ["mongodb"],
        "version": "1.0.0"
    }), 200

# ENDPOINT: GET USER ROLE
@app.route("/api/module05/user-role", methods=["GET"])
@jwt_required
def get_user_role():
    user = request.user_payload
    send_log(MODULE_NAME, "INFO", user["user_id"], "", "user_role_checked", {"role": user["role"]})
    return success_response(data={"user_id": user["user_id"], "role": user["role"]})

# ENDPOINT: CHECK PERMISSION (Core Authorization Service)
@app.route("/api/module05/check-permission", methods=["GET"])
@jwt_required
def check_permission():
    user = request.user_payload
    user_id = user["user_id"]
    jwt_role = user["role"]
    action = request.args.get("action")

    if not action:
        return error_response(400, "Missing 'action' query parameter")

    # Cross-check role with users coll. for dual ver. in case token is not in sync with DB
    try:
        db = get_db()
        db_user = db[COLLECTIONS["users"]].find_one({"_id": ObjectId(user_id)})
        current_role = db_user.get("role", jwt_role) if db_user else jwt_role
    except:
        current_role = jwt_role

    #  Validate action against role Permissions
    allowed_actions = PERMISSIONS.get(current_role, [])

    if action in allowed_actions:
        send_log(MODULE_NAME, "INFO", user_id, "", "permission_granted", {"action": action})
        return success_response(data={"granted": True, "action": action})
    else:
        send_log(MODULE_NAME, "SECURITY", user_id, "", "permission_denied", 
                 {"action": action, "role": current_role})
        return error_response(403, f"Forbidden: Role '{current_role}' cannot perform '{action}'")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=False)