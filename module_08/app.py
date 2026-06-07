# module_08/app.py
# =============================================
# MODULE 08: SECURE TIMER
# Server-side timing to prevent manipulation
# PORT: 5008
# =============================================
#
# SECURITY CONCEPT:
#   Timer runs on SERVER, not client.
#   Student cannot pause, rewind, or extend time
#   by manipulating their browser/device.
#
# ATTACK PREVENTED:
#   - Client-side time manipulation
#   - Browser dev tools to freeze timer
#   - System clock changes
#   - Late submissions after time ends
#
# FLOW:
#   Teacher creates exam (with duration_minutes)
#   Student starts exam → server records start_time
#   Student checks time → server calculates remaining
#   Time up OR student submits → answers saved → state = SUBMITTED
#   Late submission attempt → REJECTED
#
# RESPONSES COLLECTION FORMAT (for Module 16):
# {
#   "user_id": "string",
#   "exam_id": "string",
#   "question_id": "string",
#   "answer_text": "string"
# }
# =============================================

import sys
import os
import datetime

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

MODULE_NAME = "Module_08_SecureTimer"
PORT        = 5008


# =============================================
# HELPERS
# =============================================

def get_remaining_seconds(start_time_str: str, duration_minutes: int) -> int:
    """Calculate remaining seconds. Returns 0 if expired."""
    start_time  = datetime.datetime.fromisoformat(start_time_str.replace("Z", ""))
    end_time    = start_time + datetime.timedelta(minutes=duration_minutes)
    remaining   = (end_time - datetime.datetime.utcnow()).total_seconds()
    return max(0, int(remaining))


def is_exam_expired(start_time_str: str, duration_minutes: int) -> bool:
    return get_remaining_seconds(start_time_str, duration_minutes) == 0


def format_time(seconds: int) -> str:
    """Convert seconds to MM:SS string."""
    minutes = seconds // 60
    secs    = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def update_aggregate_exam_state(db, exam_id: str, now: datetime.datetime):
    """Keep the shared exam state aligned with all per-student timers."""
    timers = list(db["student_timers"].find(
        {"exam_id": exam_id},
        {"_id": 0, "submitted": 1}
    ))
    activations = list(db["exam_activations"].find(
        {"exam_id": exam_id},
        {"_id": 0, "state": 1}
    ))

    if activations and all(
        activation.get("state") == "SUBMITTED"
        for activation in activations
    ):
        state = "SUBMITTED"
    elif not activations and timers and all(timer.get("submitted") for timer in timers):
        state = "SUBMITTED"
    elif timers:
        state = "IN_PROGRESS"
    else:
        return

    db["exams"].update_one(
        {"exam_id": exam_id},
        {"$set": {"state": state, "updated_at": now.isoformat() + "Z"}}
    )


# =============================================
# HEALTH CHECK
# =============================================

@app.route("/api/module08/health", methods=["GET"])
def health():
    return {
        "module":       MODULE_NAME,
        "status":       "healthy",
        "dependencies": ["mongodb"],
        "version":      "1.0.0"
    }, 200


# =============================================
# CREATE EXAM WITH DURATION (Teacher)
# POST /api/module08/create-exam
# Role: teacher
#
# Request Body:
# {
#   "exam_id": "exam001",
#   "exam_title": "Mid Term CS101",
#   "duration_minutes": 60,
#   "total_questions": 20
# }
# =============================================

@app.route("/api/module08/create-exam", methods=["POST"])
@jwt_required
@role_required(["teacher"])
def create_exam():
    data = request.get_json()

    required = ["exam_id", "exam_title", "duration_minutes"]
    for field in required:
        if not data or field not in data:
            return error_response(400, f"Missing field: {field}")

    if data["duration_minutes"] <= 0 or data["duration_minutes"] > 300:
        return error_response(400, "duration_minutes must be between 1 and 300")

    db      = get_db()
    teacher = request.user_payload

    # Check duplicate exam
    if db["exams"].find_one({"exam_id": data["exam_id"]}):
        return error_response(409, "Exam ID already exists")

    exam_doc = {
        "exam_id":         data["exam_id"],
        "exam_title":      data["exam_title"],
        "duration_minutes": int(data["duration_minutes"]),
        "total_questions": data.get("total_questions", 0),
        "teacher_id":      teacher["user_id"],
        "state":           "NOT_STARTED",
        "created_at":      datetime.datetime.utcnow().isoformat() + "Z",
        "start_time":      None,
        "end_time":        None,
        "submitted_by":    []
    }

    db["exams"].insert_one(exam_doc)

    send_log(MODULE_NAME, "INFO", teacher["user_id"], data["exam_id"],
             "exam_created",
             {"title": data["exam_title"], "duration": data["duration_minutes"]})

    return success_response(
        data    = {
            "exam_id":          data["exam_id"],
            "exam_title":       data["exam_title"],
            "duration_minutes": data["duration_minutes"],
            "state":            "NOT_STARTED"
        },
        message = "Exam created successfully"
    )


# =============================================
# START TIMER (Student — begins exam)
# POST /api/module08/start-timer
# Role: student
#
# Request Body:
# {
#   "exam_id": "exam001"
# }
# =============================================

@app.route("/api/module08/start-timer", methods=["POST"])
@jwt_required
@role_required(["student"])
def start_timer():
    data = request.get_json()

    if not data or "exam_id" not in data:
        return error_response(400, "exam_id is required")

    exam_id = data["exam_id"]
    student = request.user_payload
    db      = get_db()

    exam = db["exams"].find_one({"exam_id": exam_id})

    if not exam:
        return error_response(404, "Exam not found")

    # Check exam state — must be ACTIVATION_VALID to start
    # Check if student already started
    student_timer = db["student_timers"].find_one({
        "user_id": student["user_id"],
        "exam_id": exam_id
    })

    if student_timer:
        if student_timer.get("submitted"):
            return error_response(409, "Exam already submitted")

        # Already started — return remaining time
        remaining = get_remaining_seconds(
            student_timer["start_time"],
            exam["duration_minutes"]
        )

        if remaining == 0:
            return error_response(409, "Exam time has already expired")

        return success_response(
            data = {
                "exam_id":          exam_id,
                "already_started":  True,
                "start_time":       student_timer["start_time"],
                "duration_minutes": exam["duration_minutes"],
                "remaining_seconds": remaining,
                "remaining_display": format_time(remaining),
                "end_time":         student_timer["end_time"]
            },
            message = "Timer already running"
        )

    activation = db["exam_activations"].find_one({
        "user_id": student["user_id"],
        "exam_id": exam_id,
        "state": "ACTIVATION_VALID"
    })
    activation_records_exist = db["exam_activations"].count_documents(
        {"exam_id": exam_id},
        limit=1
    ) > 0
    valid_states = ["ACTIVATION_VALID", "IN_PROGRESS"]
    if not activation and (
        activation_records_exist or exam.get("state") not in valid_states
    ):
        send_log(MODULE_NAME, "SECURITY", student["user_id"], exam_id,
                 "timer_start_wrong_state",
                 {"current_state": exam.get("state")})
        return error_response(409,
            f"Cannot start exam. Current state: {exam.get('state')}. "
            f"Required: ACTIVATION_VALID"
        )

    # Start fresh timer
    now      = datetime.datetime.utcnow()
    end_time = now + datetime.timedelta(minutes=exam["duration_minutes"])

    timer_doc = {
        "user_id":          student["user_id"],
        "username":         student["username"],
        "exam_id":          exam_id,
        "start_time":       now.isoformat() + "Z",
        "end_time":         end_time.isoformat() + "Z",
        "duration_minutes": exam["duration_minutes"],
        "submitted":        False,
        "auto_submitted":   False
    }

    db["student_timers"].insert_one(timer_doc)

    db["exam_activations"].update_one(
        {"user_id": student["user_id"], "exam_id": exam_id},
        {"$set": {
            "state": "IN_PROGRESS",
            "started_at": now.isoformat() + "Z"
        }}
    )

    # Update exam state to IN_PROGRESS
    db["exams"].update_one(
        {"exam_id": exam_id},
        {"$set": {
            "state":      "IN_PROGRESS",
            "updated_at": now.isoformat() + "Z"
        }}
    )

    send_log(MODULE_NAME, "INFO", student["user_id"], exam_id,
             "exam_timer_started",
             {
                 "start_time":       now.isoformat(),
                 "end_time":         end_time.isoformat(),
                 "duration_minutes": exam["duration_minutes"]
             })

    return success_response(
        data = {
            "exam_id":           exam_id,
            "start_time":        now.isoformat() + "Z",
            "end_time":          end_time.isoformat() + "Z",
            "duration_minutes":  exam["duration_minutes"],
            "remaining_seconds": exam["duration_minutes"] * 60,
            "remaining_display": format_time(exam["duration_minutes"] * 60),
            "state":             "IN_PROGRESS"
        },
        message = "Timer started. Exam is now IN_PROGRESS."
    )


# =============================================
# GET REMAINING TIME (Student)
# GET /api/module08/time-remaining/<exam_id>
# Role: student
# =============================================

@app.route("/api/module08/time-remaining/<exam_id>", methods=["GET"])
@jwt_required
@role_required(["student"])
def time_remaining(exam_id):
    student = request.user_payload
    db      = get_db()

    timer = db["student_timers"].find_one({
        "user_id": student["user_id"],
        "exam_id": exam_id
    })

    if not timer:
        return error_response(404, "Timer not started for this exam")

    if timer.get("submitted"):
        return success_response(
            data    = {"exam_id": exam_id, "submitted": True, "remaining_seconds": 0},
            message = "Exam already submitted"
        )

    exam      = db["exams"].find_one({"exam_id": exam_id})
    remaining = get_remaining_seconds(timer["start_time"], exam["duration_minutes"])

    # Auto-submit if time expired
    if remaining == 0 and not timer.get("submitted"):
        _auto_submit(student["user_id"], exam_id, db)
        return success_response(
            data = {
                "exam_id":           exam_id,
                "remaining_seconds": 0,
                "remaining_display": "00:00",
                "expired":           True,
                "auto_submitted":    True
            },
            message = "Time expired. Exam auto-submitted."
        )

    # Warning logs at 5 min and 1 min remaining
    if remaining == 300:
        send_log(MODULE_NAME, "WARNING", student["user_id"], exam_id,
                 "timer_5min_warning", {"remaining": 300})
    elif remaining == 60:
        send_log(MODULE_NAME, "WARNING", student["user_id"], exam_id,
                 "timer_1min_warning", {"remaining": 60})

    return success_response(
        data = {
            "exam_id":           exam_id,
            "remaining_seconds": remaining,
            "remaining_display": format_time(remaining),
            "end_time":          timer["end_time"],
            "expired":           False
        },
        message = "Time remaining retrieved"
    )


# =============================================
# SUBMIT EXAM (Student)
# POST /api/module08/submit-exam
# Role: student
#
# Request Body:
# {
#   "exam_id": "exam001",
#   "answers": [
#     {"question_id": "q1", "answer_text": "Paris"},
#     {"question_id": "q2", "answer_text": "Newton"}
#   ]
# }
# =============================================

@app.route("/api/module08/submit-exam", methods=["POST"])
@jwt_required
@role_required(["student"])
def submit_exam():
    data    = request.get_json()
    student = request.user_payload

    if not data or "exam_id" not in data:
        return error_response(400, "exam_id is required")

    exam_id = data["exam_id"]
    answers = data.get("answers", [])
    db      = get_db()

    # Get timer
    timer = db["student_timers"].find_one({
        "user_id": student["user_id"],
        "exam_id": exam_id
    })

    if not timer:
        return error_response(404, "Timer not found. Did you start the exam?")

    # Already submitted
    if timer.get("submitted"):
        return error_response(409, "Exam already submitted")

    # Get exam
    exam = db["exams"].find_one({"exam_id": exam_id})
    if not exam:
        return error_response(404, "Exam not found")
    if exam.get("state") != "IN_PROGRESS":
        return error_response(
            409,
            f"Answer submission requires IN_PROGRESS state. Current state: {exam.get('state')}"
        )


    # Check time — reject late submission
    remaining = get_remaining_seconds(timer["start_time"], exam["duration_minutes"])
    if remaining == 0:
        send_log(MODULE_NAME, "SECURITY", student["user_id"], exam_id,
                 "late_submission_attempt", {"remaining": 0})
        # Auto-submit whatever was answered
        _auto_submit(student["user_id"], exam_id, db)
        return error_response(409,
            "Time expired. Late submission rejected. Your answers were auto-submitted when time ran out."
        )

    now = datetime.datetime.utcnow()

    # Save answers to responses collection (Module 16 reads from here)
    if answers:
        response_docs = []
        for ans in answers:
            if "question_id" not in ans or "answer_text" not in ans:
                continue
            response_docs.append({
                "user_id":     student["user_id"],
                "exam_id":     exam_id,
                "question_id": ans["question_id"],
                "answer_text": str(ans["answer_text"])[:5000],  # cap at 5000 chars
                "submitted_at": now.isoformat() + "Z"
            })

        if response_docs:
            # Remove old answers first (in case of resubmission attempt)
            db["responses"].delete_many({
                "user_id": student["user_id"],
                "exam_id": exam_id
            })
            db["responses"].insert_many(response_docs)

    # Mark timer as submitted
    time_taken = int((now - datetime.datetime.fromisoformat(
        timer["start_time"].replace("Z", "")
    )).total_seconds())

    db["student_timers"].update_one(
        {"user_id": student["user_id"], "exam_id": exam_id},
        {"$set": {
            "submitted":    True,
            "submitted_at": now.isoformat() + "Z",
            "time_taken_seconds": time_taken
        }}
    )

    db["exam_activations"].update_one(
        {"user_id": student["user_id"], "exam_id": exam_id},
        {"$set": {
            "state": "SUBMITTED",
            "submitted_at": now.isoformat() + "Z"
        }}
    )

    db["exams"].update_one(
        {"exam_id": exam_id},
        {
            "$addToSet": {"submitted_by": student["user_id"]}
        }
    )
    update_aggregate_exam_state(db, exam_id, now)

    send_log(MODULE_NAME, "INFO", student["user_id"], exam_id,
             "exam_submitted",
             {
                 "answers_count":     len(answers),
                 "time_taken_seconds": time_taken,
                 "remaining_seconds": remaining
             })

    return success_response(
        data = {
            "exam_id":            exam_id,
            "submitted":          True,
            "answers_saved":      len(answers),
            "time_taken_seconds": time_taken,
            "time_taken_display": format_time(time_taken),
            "submitted_at":       now.isoformat() + "Z"
        },
        message = "Exam submitted successfully."
    )


# =============================================
# INTERNAL AUTO-SUBMIT
# Called when timer expires
# =============================================

def _auto_submit(user_id: str, exam_id: str, db):
    """Auto-submit exam when time expires."""
    now = datetime.datetime.utcnow()

    db["student_timers"].update_one(
        {"user_id": user_id, "exam_id": exam_id},
        {"$set": {
            "submitted":      True,
            "auto_submitted": True,
            "submitted_at":   now.isoformat() + "Z"
        }}
    )

    db["exam_activations"].update_one(
        {"user_id": user_id, "exam_id": exam_id},
        {"$set": {
            "state": "SUBMITTED",
            "submitted_at": now.isoformat() + "Z"
        }}
    )

    db["exams"].update_one(
        {"exam_id": exam_id},
        {
            "$addToSet": {"submitted_by": user_id}
        }
    )
    update_aggregate_exam_state(db, exam_id, now)

    send_log(MODULE_NAME, "WARNING", user_id, exam_id,
             "exam_auto_submitted_time_expired", {})


# =============================================
# EXAM STATUS — All Students (Teacher)
# GET /api/module08/exam-status/<exam_id>
# Role: teacher
# =============================================

@app.route("/api/module08/exam-status/<exam_id>", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def exam_status(exam_id):
    db   = get_db()
    exam = db["exams"].find_one({"exam_id": exam_id}, {"_id": 0})

    if not exam:
        return error_response(404, "Exam not found")

    # Get all student timers for this exam
    timers = list(db["student_timers"].find(
        {"exam_id": exam_id},
        {"_id": 0}
    ))

    # Add remaining time for active students
    for t in timers:
        if not t.get("submitted"):
            t["remaining_seconds"] = get_remaining_seconds(
                t["start_time"], exam["duration_minutes"]
            )
            t["remaining_display"] = format_time(t["remaining_seconds"])
        else:
            t["remaining_seconds"] = 0

    submitted = sum(1 for t in timers if t.get("submitted"))
    active    = sum(1 for t in timers if not t.get("submitted"))

    return success_response(
        data = {
            "exam_id":          exam_id,
            "exam_title":       exam.get("exam_title"),
            "state":            exam.get("state"),
            "duration_minutes": exam.get("duration_minutes"),
            "summary": {
                "total_students": len(timers),
                "submitted":      submitted,
                "active":         active,
            },
            "students": timers
        },
        message = "Exam status retrieved"
    )


# =============================================
# RISK DATA — For Module 17
# GET /api/module08/risk-data?user_id=X&exam_id=Y
# =============================================

@app.route("/api/module08/risk-data", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def risk_data():
    user_id = request.args.get("user_id")
    exam_id = request.args.get("exam_id")

    if not user_id or not exam_id:
        return error_response(400, "user_id and exam_id are required")

    db    = get_db()
    timer = db["student_timers"].find_one({
        "user_id": user_id,
        "exam_id": exam_id
    })

    exam = db["exams"].find_one({"exam_id": exam_id})

    fast_answer_flag = 0
    if timer and exam:
        time_taken = timer.get("time_taken_seconds", 0)
        total_time = exam.get("duration_minutes", 60) * 60
        # Flag if submitted in less than 20% of total time
        if time_taken > 0 and time_taken < (total_time * 0.2):
            fast_answer_flag = 1

    return success_response(
        data = {
            "module": MODULE_NAME,
            "data": [{
                "user_id":   user_id,
                "exam_id":   exam_id,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "metric":    "fast_answering",
                "value":     fast_answer_flag
            }]
        },
        message = "Risk data retrieved"
    )


if __name__ == "__main__":
    print(f"🔐 Module 08 — Secure Timer running on port {PORT}")
    print(f"   POST /api/module08/create-exam       (teacher)")
    print(f"   POST /api/module08/start-timer       (student)")
    print(f"   GET  /api/module08/time-remaining/<exam_id>  (student)")
    print(f"   POST /api/module08/submit-exam       (student)")
    print(f"   GET  /api/module08/exam-status/<exam_id>  (teacher)")
    print(f"   GET  /api/module08/risk-data         (module 17)")
    print(f"   GET  /api/module08/health")
    app.run(port=PORT, debug=True)
