"""Focused regression test for the multi-student exam workflow."""

import datetime

import jwt
import requests
from pymongo import MongoClient


BASE_URL = "http://127.0.0.1"
EXAM_ID = "regression_exam_001"
JWT_SECRET = "exam_security_UET_2024_secret_key"
JWT_ALGORITHM = "HS256"
USER_IDS = ["regression_teacher", "regression_student_1", "regression_student_2"]


def make_token(user_id, role):
    return jwt.encode(
        {
            "user_id": user_id,
            "username": user_id,
            "role": role,
            "session_id": f"session_{user_id}",
            "device_fingerprint_hash": "",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def request(method, port, path, token, body=None, params=None):
    response = requests.request(
        method,
        f"{BASE_URL}:{port}{path}",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
        params=params,
        timeout=20,
    )
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw": response.text}
    return response.status_code, payload


def response_data(payload):
    return payload.get("data", {})


def expect(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def cleanup(db):
    for collection in [
        "exams",
        "activation_codes",
        "exam_activations",
        "questions",
        "responses",
        "student_timers",
        "question_orders",
        "risk_scores",
        "similarity_results",
        "tab_events",
        "clipboard_events",
        "activity_logs",
        "active_sessions",
        "behavior_events",
        "behavior_analysis",
    ]:
        db[collection].delete_many({"exam_id": EXAM_ID})
    db["logs"].delete_many({
        "$or": [
            {"exam_id": EXAM_ID},
            {"user_id": {"$in": USER_IDS}},
        ]
    })


def main():
    db = MongoClient("mongodb://localhost:27017/")["exam_security"]
    teacher = make_token(USER_IDS[0], "teacher")
    student_1 = make_token(USER_IDS[1], "student")
    student_2 = make_token(USER_IDS[2], "student")

    cleanup(db)
    try:
        db["exams"].insert_one({
            "exam_id": EXAM_ID,
            "exam_title": "Regression Exam",
            "duration_minutes": 30,
            "teacher_id": USER_IDS[0],
            "state": "NOT_STARTED",
            "submitted_by": [],
        })
        db["questions"].insert_many([
            {
                "exam_id": EXAM_ID,
                "question_id": f"q{index}",
                "question_text": f"Question {index}",
                "released": True,
            }
            for index in range(1, 4)
        ])

        codes = []
        for _ in range(2):
            status, payload = request(
                "POST",
                5004,
                "/api/module04/generate-code",
                teacher,
                {"exam_id": EXAM_ID},
            )
            expect(status == 200, "teacher can generate an activation code")
            codes.append(response_data(payload)["code"])

        status, payload = request(
            "POST",
            5004,
            "/api/module04/validate-code",
            student_1,
            {"exam_id": EXAM_ID, "code": codes[0]},
        )
        expect(
            status == 200
            and response_data(payload).get("state") == "ACTIVATION_VALID",
            "activation validation returns the documented state",
        )

        status, _ = request(
            "POST",
            5004,
            "/api/module04/validate-code",
            student_1,
            {"exam_id": EXAM_ID, "code": "WRONGCOD"},
        )
        expect(status == 401, "invalid activation code returns HTTP 401")

        status, _ = request(
            "POST",
            5004,
            "/api/module04/validate-code",
            student_2,
            {"exam_id": EXAM_ID, "code": codes[1]},
        )
        expect(status == 200, "second student can validate an activation code")

        for token in [student_1, student_2]:
            status, _ = request(
                "POST",
                5008,
                "/api/module08/start-timer",
                token,
                {"exam_id": EXAM_ID},
            )
            expect(status == 200, "activated student can start a timer")

        orders = []
        for token in [student_1, student_2]:
            status, payload = request(
                "GET",
                5007,
                f"/api/module07/randomized-questions/{EXAM_ID}",
                token,
            )
            order = [
                question["question_id"]
                for question in response_data(payload).get("questions", [])
            ]
            expect(status == 200 and len(order) == 3, "student receives three questions")
            orders.append(order)
        expect(orders[0] != orders[1], "students receive different question orders")

        answers = [
            {"question_id": f"q{index}", "answer_text": f"Identical answer {index}"}
            for index in range(1, 4)
        ]
        status, _ = request(
            "POST",
            5008,
            "/api/module08/submit-exam",
            student_1,
            {"exam_id": EXAM_ID, "answers": answers},
        )
        expect(status == 200, "first student can submit")

        status, payload = request(
            "POST",
            5008,
            "/api/module08/start-timer",
            student_2,
            {"exam_id": EXAM_ID},
        )
        expect(
            status == 200 and response_data(payload).get("already_started") is True,
            "first submission does not terminate another student's timer",
        )

        status, _ = request(
            "POST",
            5008,
            "/api/module08/submit-exam",
            student_2,
            {"exam_id": EXAM_ID, "answers": answers},
        )
        expect(status == 200, "second student can submit after the first student")
        expect(
            db["responses"].count_documents({"exam_id": EXAM_ID}) == 6,
            "all six answers are persisted",
        )

        status, payload = request(
            "POST",
            5016,
            "/api/module16/check-similarity",
            teacher,
            {"exam_id": EXAM_ID},
        )
        expect(
            status == 200 and response_data(payload).get("flagged_pairs", 0) > 0,
            "identical answers are flagged by similarity analysis",
        )

        validation_cases = [
            ({"exam_id": {"$gt": ""}, "answer": "normal text"}, 400, "nosql_injection"),
            ({"answer": "<script>alert('xss')</script>"}, 400, "xss"),
            ({"answer": "This is a clean normal answer about security"}, 200, None),
        ]
        for body, expected_status, expected_message in validation_cases:
            status, payload = request(
                "POST",
                5009,
                "/api/module09/validate-input",
                student_1,
                body,
            )
            expect(status == expected_status, f"validation returns HTTP {expected_status}")
            if expected_message:
                expect(
                    expected_message in payload.get("message", ""),
                    f"validation identifies {expected_message}",
                )
            else:
                expect(
                    response_data(payload).get("safe") is True,
                    "clean input is marked safe",
                )

        status, _ = request(
            "GET",
            5017,
            f"/api/module17/risk-score/{USER_IDS[1]}/{EXAM_ID}",
            teacher,
        )
        expect(status == 200, "risk score can be calculated")

        status, payload = request(
            "GET",
            5017,
            "/api/module17/dashboard",
            teacher,
            params={"exam_id": EXAM_ID},
        )
        expect(
            status == 200 and response_data(payload).get("total_students") == 2,
            "dashboard calculates and returns both participants",
        )
    finally:
        cleanup(db)


if __name__ == "__main__":
    main()
