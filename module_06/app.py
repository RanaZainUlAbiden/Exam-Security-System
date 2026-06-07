import sys
import os
import datetime
import hashlib
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response
from shared.exam_state_helper import active_exam_error

app = Flask(__name__)
MODULE_NAME = "Module_06_QuestionDelivery"
PORT = 5006

@app.route("/api/module06/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

@app.route("/api/module06/add-questions", methods=["POST"])
@jwt_required
@role_required(["teacher"])
def add_questions():
    data = request.get_json()
    if not data or "exam_id" not in data or "questions" not in data:
        return error_response(400, "exam_id and questions required")

    db = get_db()
    teacher = request.user_payload
    now = datetime.datetime.utcnow()
    docs = []

    for q in data["questions"]:
        if "question_text" not in q:
            continue
        q_id = hashlib.md5(f"{data['exam_id']}{q['question_text']}{now.isoformat()}".encode()).hexdigest()[:12]
        docs.append({
            "question_id": q_id,
            "exam_id": data["exam_id"],
            "question_text": q["question_text"],
            "question_type": q.get("question_type", "text"),
            "options": q.get("options", []),
            "marks": q.get("marks", 1),
            "teacher_id": teacher["user_id"],
            "created_at": now.isoformat() + "Z",
            "released": False
        })

    if docs:
        db["questions"].insert_many(docs)

    send_log(MODULE_NAME, "INFO", teacher["user_id"], data["exam_id"],
             "questions_added", {"count": len(docs)})

    return success_response(
        data={"exam_id": data["exam_id"], "questions_added": len(docs)},
        message=f"{len(docs)} questions added"
    )

@app.route("/api/module06/release-questions", methods=["POST"])
@jwt_required
@role_required(["teacher"])
def release_questions():
    data = request.get_json()
    if not data or "exam_id" not in data:
        return error_response(400, "exam_id required")

    db = get_db()
    result = db["questions"].update_many(
        {"exam_id": data["exam_id"]},
        {"$set": {"released": True}}
    )
    send_log(MODULE_NAME, "INFO", request.user_payload["user_id"], data["exam_id"],
             "questions_released", {"count": result.modified_count})
    return success_response(data={"released": result.modified_count}, message="Questions released")

@app.route("/api/module06/questions/<exam_id>", methods=["GET"])
@jwt_required
def get_questions(exam_id):
    db = get_db()
    user = request.user_payload

    # Check exam is IN_PROGRESS for students
    if user["role"] == "student":
        state_error = active_exam_error(db, user["user_id"], exam_id)
        if state_error:
            send_log(MODULE_NAME, "SECURITY", user["user_id"], exam_id,
                     "question_access_denied", {"reason": state_error})
            return error_response(403, state_error)

    questions = list(db["questions"].find(
        {"exam_id": exam_id, "released": True},
        {"_id": 0, "teacher_id": 0}  # hide teacher info from students
    ))

    send_log(MODULE_NAME, "INFO", user["user_id"], exam_id,
             "questions_accessed", {"count": len(questions)})

    return success_response(
        data={"exam_id": exam_id, "questions": questions, "total": len(questions)},
        message="Questions delivered"
    )

if __name__ == "__main__":
    print(f"Module 06 — Question Delivery running on port {PORT}")
    app.run(port=PORT, debug=True)
