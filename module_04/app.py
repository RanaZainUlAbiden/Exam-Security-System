import sys
import os
import datetime
import random
import string
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

app = Flask(__name__)

MODULE_NAME = "Module_04_Activation_Code"
PORT        = 5004

@app.route("/api/module04/health", methods=["GET"])
def health():
    return jsonify({
        "module":       MODULE_NAME,
        "status":       "healthy",
        "dependencies": ["mongodb"],
        "version":      "1.0.0"
    }), 200

@app.route("/api/module04/generate-code", methods=["POST"])
@jwt_required
@role_required(["teacher"])
def generate_code():
    data = request.get_json()
    if not data or "exam_id" not in data:
        return error_response(400, "exam_id required")
    
    exam_id = data["exam_id"]
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    now = datetime.datetime.utcnow()
    expires_at = now + datetime.timedelta(minutes=10)
    
    db = get_db()
    db["activation_codes"].insert_one({
        "code": code,
        "exam_id": exam_id,
        "expires_at": expires_at.isoformat() + "Z",
        "used": False,
        "created_by": request.user_payload["user_id"],
        "created_at": now.isoformat() + "Z"
    })
    
    send_log(MODULE_NAME, "INFO", request.user_payload["user_id"], exam_id,
             "activation_code_generated", {"expires_at": expires_at.isoformat() + "Z"})
             
    return success_response(
        data={"code": code, "exam_id": exam_id, "expires_at": expires_at.isoformat() + "Z"},
        message="Activation code generated"
    )

@app.route("/api/module04/validate-code", methods=["POST"])
@jwt_required
@role_required(["student"])
def validate_code():
    data = request.get_json()
    if not data or "code" not in data or "exam_id" not in data:
        return error_response(400, "code and exam_id required")
        
    code = data["code"]
    exam_id = data["exam_id"]
    user_id = request.user_payload["user_id"]
    db = get_db()
    
    doc = db["activation_codes"].find_one({"code": code, "exam_id": exam_id})
    if not doc:
        send_log(MODULE_NAME, "WARNING", user_id, exam_id, "invalid_code_attempt", {"code": code})
        return error_response(404, "Invalid activation code")
        
    if doc["used"]:
        send_log(MODULE_NAME, "WARNING", user_id, exam_id, "used_code_attempt", {"code": code})
        return error_response(409, "Activation code already used")
        
    expires_at = datetime.datetime.fromisoformat(doc["expires_at"].replace("Z", ""))
    if datetime.datetime.utcnow() > expires_at:
        send_log(MODULE_NAME, "WARNING", user_id, exam_id, "expired_code_attempt", {"code": code})
        return error_response(410, "Activation code expired")
        
    db["activation_codes"].update_one(
        {"_id": doc["_id"]},
        {"$set": {"used": True, "used_by": user_id, "used_at": datetime.datetime.utcnow().isoformat() + "Z"}}
    )
    
    db["exams"].update_one(
        {"exam_id": exam_id},
        {"$set": {"state": "ACTIVATION_VALID", "updated_at": datetime.datetime.utcnow().isoformat() + "Z"}},
        upsert=True
    )
    
    send_log(MODULE_NAME, "INFO", user_id, exam_id, "activation_code_validated", {})
    return success_response(data={"valid": True, "exam_id": exam_id}, message="Activation code validated successfully")

@app.route("/api/module04/code-status/<code>", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def code_status(code):
    db = get_db()
    doc = db["activation_codes"].find_one({"code": code}, {"_id": 0})
    if not doc:
        return error_response(404, "Code not found")
        
    return success_response(data=doc, message="Code status retrieved")

@app.route("/api/module04/risk-data", methods=["GET"])
@jwt_required
def risk_data():
    user_id = request.args.get("user_id")
    exam_id = request.args.get("exam_id")
    if not user_id or not exam_id:
        return error_response(400, "user_id and exam_id required")

    return success_response(data={"module": MODULE_NAME, "data": []}, message="Risk data retrieved")

if __name__ == "__main__":
    print(f"🔐 Module 04 — Activation Code Security running on port {PORT}")
    app.run(port=PORT, debug=True)
