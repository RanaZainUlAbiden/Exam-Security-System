def active_exam_error(db, user_id: str, exam_id: str):
    """Return an error message unless this student's exam timer is active."""
    exam = db["exams"].find_one({"exam_id": exam_id}, {"state": 1})
    if not exam:
        return "Exam not found"

    timer = db["student_timers"].find_one(
        {"user_id": user_id, "exam_id": exam_id},
        {"submitted": 1},
    )
    if not timer or timer.get("submitted") or exam.get("state") != "IN_PROGRESS":
        return (
            f"Exam monitoring requires IN_PROGRESS state. "
            f"Current state: {exam.get('state', 'UNKNOWN')}"
        )

    return None
