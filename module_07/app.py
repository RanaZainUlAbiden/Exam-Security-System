<<<<<<< Updated upstream
import sys
import os
import hashlib
import hmac
import random
import datetime
import json
=======
# module_07/app.py
# MODULE 07: QUESTION RANDOMIZATION — Anti-collusion
# PORT: 5007
>>>>>>> Stashed changes

import sys, os, datetime, random, hashlib
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

app = Flask(__name__)
MODULE_NAME = "Module_07_QuestionRandomization"
PORT = 5007

<<<<<<< Updated upstream
MODULE_NAME = "Module_07_Question_Randomization"
PORT        = 5007

SEED_HMAC_SECRET = b"exam_security_UET_2024_secret_key"


def _derive_seed(user_id: str, exam_id: str, session_id: str) -> int:
    message = f"{user_id}|{exam_id}|{session_id}".encode()
    digest  = hmac.new(SEED_HMAC_SECRET, message, hashlib.sha256).digest()
    seed    = int.from_bytes(digest[:8], "big")
    return seed


def _shuffle_with_seed(items: list, seed: int) -> list:
    lst = list(items)
    rng = random.Random(seed)
    rng.shuffle(lst)
    return lst


def _get_exam_state(exam_id: str):
   
    try:
        db   = get_db()
        exam = db["exams"].find_one({"exam_id": exam_id})
        if exam:
            return exam.get("state", "UNKNOWN")
        return None
    except Exception:
        return None

@app.route("/api/module07/health", methods=["GET"])
def health():
    """No JWT required — integration test calls this directly."""
    db_ok = False
    try:
        db = get_db()
        db.list_collection_names()  
        db_ok = True
    except Exception:
        pass

    return jsonify({
        "module":       MODULE_NAME,
        "status":       "healthy" if db_ok else "degraded",
        "dependencies": ["mongodb"],
        "version":      "1.0.0"
    }), 200

@app.route("/api/module07/randomized-questions/<exam_id>", methods=["GET"])
@jwt_required
def get_randomized_questions(exam_id: str):
    
    user    = request.user_payload
    user_id = user["user_id"]
    role    = user.get("role", "")
    session_id = user.get("session_id", "default")

    if role != "student":
        send_log(MODULE_NAME, "SECURITY", user_id, exam_id,
                 "unauthorized_role_attempt",
                 {"role": role, "required": "student"})
        return error_response(403, "Only students can fetch randomized questions")

    if not exam_id or not exam_id.strip():
        return error_response(400, "exam_id is required")

    db = get_db()

    state = _get_exam_state(exam_id)
    if state is None:
        return error_response(404, f"Exam '{exam_id}' not found")
    if state != "IN_PROGRESS":
        send_log(MODULE_NAME, "WARNING", user_id, exam_id,
                 "wrong_exam_state_access",
                 {"current_state": state, "required": "IN_PROGRESS"})
        return error_response(409,
            f"Exam is not in progress. Current state: {state}. "
            "Questions can only be fetched during IN_PROGRESS.")

    try:
        questions_cursor = db["questions"].find(
            {"exam_id": exam_id},
            {"_id": 0}  
        )
        questions = list(questions_cursor)
    except Exception as e:
        send_log(MODULE_NAME, "ERROR", user_id, exam_id,
                 "db_fetch_error", {"error": str(e)})
        return error_response(500, "Failed to fetch questions from database")

    if not questions:
        return error_response(404,
            f"No questions found for exam '{exam_id}'. "
            "Ensure Module 6 has loaded questions first.")

    seed = _derive_seed(user_id, exam_id, session_id)

    shuffled_questions = _shuffle_with_seed(questions, seed)

    processed_questions = []
    original_positions  = []  

    for shuffled_idx, q in enumerate(shuffled_questions):
        q_seed = seed ^ (hash(q.get("question_id", str(shuffled_idx))) & 0xFFFFFFFF)

        original_options = q.get("options", [])
        shuffled_options = _shuffle_with_seed(original_options, q_seed)

        option_mapping = []
        for new_pos, opt in enumerate(shuffled_options):
            try:
                orig_pos = original_options.index(opt)
            except ValueError:
                orig_pos = new_pos  
            option_mapping.append({"shuffled_pos": new_pos, "original_pos": orig_pos})

        processed_questions.append({
            "shuffled_index":   shuffled_idx,       
            "question_id":      q.get("question_id"),   
            "question_text":    q.get("question_text", ""),
            "options":          shuffled_options,
            "marks":            q.get("marks", 1),
            "question_type":    q.get("question_type", "mcq"),
        })

        original_positions.append({
            "shuffled_index":   shuffled_idx,
            "question_id":      q.get("question_id"),
            "original_index":   questions.index(q) if q in questions else -1,
            "option_mapping":   option_mapping,
        })

    mapping_doc = {
        "user_id":       user_id,
        "exam_id":       exam_id,
        "session_id":    session_id,
        "seed":          str(seed),    
        "total_questions": len(questions),
        "mapping":       original_positions,
        "created_at":    datetime.datetime.utcnow().isoformat() + "Z",
    }
    try:
        db["randomization_maps"].update_one(
            {"user_id": user_id, "exam_id": exam_id, "session_id": session_id},
            {"$set": mapping_doc},
            upsert=True
        )
    except Exception as e:
        send_log(MODULE_NAME, "WARNING", user_id, exam_id,
                 "mapping_persist_failed", {"error": str(e)})

    send_log(MODULE_NAME, "INFO", user_id, exam_id,
             "questions_randomized",
             {
                 "total_questions": len(questions),
                 "seed_hash":       hashlib.sha256(str(seed).encode()).hexdigest()[:16],
                 "session_id":      session_id,
             })

    return success_response(
        data={
            "exam_id":         exam_id,
            "total_questions": len(processed_questions),
            "questions":       processed_questions,
        },
        message="Questions randomized successfully. Each student receives a unique order."
    )

@app.route("/api/module07/shuffle-mapping/<exam_id>", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def get_shuffle_mapping(exam_id: str):
   
    user    = request.user_payload
    user_id = user["user_id"]

    filter_user_id = request.args.get("user_id")

    db    = get_db()
    query = {"exam_id": exam_id}
    if filter_user_id:
        query["user_id"] = filter_user_id

    try:
        mappings = list(db["randomization_maps"].find(query, {"_id": 0}))
    except Exception as e:
        return error_response(500, f"Database error: {str(e)}")

    send_log(MODULE_NAME, "INFO", user_id, exam_id,
             "teacher_viewed_mappings",
             {"count": len(mappings), "filter_user": filter_user_id})

    return success_response(
        data={
            "exam_id":      exam_id,
            "total_maps":   len(mappings),
            "mappings":     mappings,
        },
        message="Shuffle mappings retrieved"
    )

@app.route("/api/module07/verify-seed/<exam_id>", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def verify_seed(exam_id: str):

    target_user_id = request.args.get("user_id")
    target_session  = request.args.get("session_id", "default")

    if not target_user_id:
        return error_response(400, "user_id query parameter required")

    seed       = _derive_seed(target_user_id, exam_id, target_session)
    seed_proof = hashlib.sha256(str(seed).encode()).hexdigest()

    send_log(MODULE_NAME, "INFO", request.user_payload["user_id"], exam_id,
             "seed_verification_requested",
             {"target_user": target_user_id, "seed_hash": seed_proof})

    return success_response(
        data={
            "user_id":    target_user_id,
            "exam_id":    exam_id,
            "session_id": target_session,
            "seed_proof": seed_proof,   
        },
        message="Seed verification hash generated. Compare with stored mapping's seed hash."
    )


@app.route("/api/module07/seed-questions", methods=["POST"])
@jwt_required
@role_required(["teacher"])
def seed_questions():
  
    body    = request.get_json(silent=True) or {}
    exam_id = body.get("exam_id")

    if not exam_id:
        return error_response(400, "exam_id is required")

    sample_questions = [
        {
            "question_id":   f"{exam_id}_q{i}",
            "exam_id":       exam_id,
            "question_text": f"Sample Question {i}: What is the correct answer?",
            "options":       [f"Option A{i}", f"Option B{i}", f"Option C{i}", f"Option D{i}"],
            "correct_index": 0, 
            "marks":         2,
            "question_type": "mcq",
        }
        for i in range(1, 11)   
    ]

    db = get_db()
    try:
        db["questions"].delete_many({"exam_id": exam_id})
        db["questions"].insert_many(sample_questions)
    except Exception as e:
        return error_response(500, f"Failed to seed questions: {str(e)}")

    send_log(MODULE_NAME, "INFO", request.user_payload["user_id"], exam_id,
             "questions_seeded_for_testing", {"count": len(sample_questions)})

    return success_response(
        data={"exam_id": exam_id, "questions_inserted": len(sample_questions)},
        message="Sample questions inserted for testing"
    )


@app.route("/api/module07/stats/<exam_id>", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def get_stats(exam_id: str):
    """Returns summary stats for teacher monitoring dashboard."""
    db = get_db()
    try:
        count         = db["randomization_maps"].count_documents({"exam_id": exam_id})
        unique_users  = db["randomization_maps"].distinct("user_id", {"exam_id": exam_id})
        total_questions = db["questions"].count_documents({"exam_id": exam_id})
    except Exception as e:
        return error_response(500, f"Stats query failed: {str(e)}")

    send_log(MODULE_NAME, "INFO", request.user_payload["user_id"], exam_id,
             "stats_viewed", {})

    return success_response(
        data={
            "exam_id":             exam_id,
            "total_questions":     total_questions,
            "students_randomized": count,
            "unique_students":     len(unique_users),
        },
        message="Stats retrieved"
    )

if __name__ == "__main__":
    print(f"\n{'='*55}")
    print(f"  🔐 Module 07 — Question Randomization")
    print(f"  Anti-Collusion Shuffling | Port {PORT}")
    print(f"{'='*55}")
    print(f"  Endpoints:")
    print(f"    GET  /api/module07/health")
    print(f"    GET  /api/module07/randomized-questions/<exam_id>")
    print(f"    GET  /api/module07/shuffle-mapping/<exam_id>")
    print(f"    GET  /api/module07/verify-seed/<exam_id>")
    print(f"    POST /api/module07/seed-questions")
    print(f"    GET  /api/module07/stats/<exam_id>")
    print(f"{'='*55}\n")
    app.run(host="0.0.0.0", port=PORT, debug=True)
=======
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
>>>>>>> Stashed changes
