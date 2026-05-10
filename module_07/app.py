import sys
import os
import datetime
import random
import hashlib
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

app = Flask(__name__)
MODULE_NAME = "Module_07_QuestionRandomization"
PORT = 5007

@app.route("/api/module07/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

@app.route("/api/module07/randomized-questions/<exam_id>", methods=["GET"])
@jwt_required
@role_required(["student"])
def randomized_questions(exam_id):
    """
    Returns questions in a unique random order per student.
    Same student always gets same order (seeded by user_id+exam_id).
    Different students get different orders — anti-collusion.
    """
    db = get_db()
    user = request.user_payload

    # Check exam state
    exam = db["exams"].find_one({"exam_id": exam_id})
    if not exam or exam.get("state") != "IN_PROGRESS":
        return error_response(403, "Questions only accessible during IN_PROGRESS exam")

    # Get questions
    questions = list(db["questions"].find(
        {"exam_id": exam_id, "released": True},
        {"_id": 0, "teacher_id": 0}
    ))

    if not questions:
        return error_response(404, "No questions found for this exam")

    # Check if this student already has a shuffled order
    existing = db["question_orders"].find_one({
        "user_id": user["user_id"],
        "exam_id": exam_id
    })

    if existing:
        # Return same order as before (consistent for same student)
        order = existing["question_order"]
        q_map = {q["question_id"]: q for q in questions}
        ordered = [q_map[qid] for qid in order if qid in q_map]
    else:
        # Create unique seed per student — same student = same order always
        seed_string = f"{user['user_id']}_{exam_id}_randomize"
        seed = int(hashlib.md5(seed_string.encode()).hexdigest(), 16) % (2**32)

        random.seed(seed)
        shuffled = questions.copy()
        random.shuffle(shuffled)
        ordered = shuffled

        # Save the order
        db["question_orders"].insert_one({
            "user_id": user["user_id"],
            "exam_id": exam_id,
            "question_order": [q["question_id"] for q in ordered],
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        })

    send_log(MODULE_NAME, "INFO", user["user_id"], exam_id,
             "randomized_questions_served", {"count": len(ordered)})

    return success_response(
        data={"exam_id": exam_id, "questions": ordered, "total": len(ordered),
              "note": "Questions are in unique order for your account"},
        message="Randomized questions delivered"
    )

if __name__ == "__main__":
    print(f"Module 07 — Question Randomization running on port {PORT}")
    app.run(port=PORT, debug=True)
