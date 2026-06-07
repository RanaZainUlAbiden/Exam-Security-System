"""Focused regression test for the multi-student exam workflow."""

import datetime
import os

import jwt
import requests
from pymongo import MongoClient


BASE_URL = "http://127.0.0.1"
SINGLE_PROCESS_BASE_URL = os.getenv("SINGLE_PROCESS_BASE_URL", "").rstrip("/")
EXAM_ID = "regression_exam_001"
AUTH_TEACHER_USERNAME = "regression_auth_teacher"
JWT_SECRET = "exam_security_UET_2024_secret_key"
JWT_ALGORITHM = "HS256"
USER_IDS = [
    "regression_teacher",
    "regression_student_1",
    "regression_student_2",
    "regression_multi_session",
]


def make_token(user_id, role, expires_in_hours=1, session_id=None):
    return jwt.encode(
        {
            "user_id": user_id,
            "username": user_id,
            "role": role,
            "session_id": session_id or f"session_{user_id}",
            "device_fingerprint_hash": "",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(
                hours=expires_in_hours
            ),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def request(method, port, path, token, body=None, params=None):
    url = (
        f"{SINGLE_PROCESS_BASE_URL}{path}"
        if SINGLE_PROCESS_BASE_URL
        else f"{BASE_URL}:{port}{path}"
    )
    response = requests.request(
        method,
        url,
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


def public_request(method, port, path, body=None):
    url = (
        f"{SINGLE_PROCESS_BASE_URL}{path}"
        if SINGLE_PROCESS_BASE_URL
        else f"{BASE_URL}:{port}{path}"
    )
    response = requests.request(method, url, json=body, timeout=20)
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
    db["blacklisted_tokens"].delete_many({"user_id": {"$in": USER_IDS}})
    db["users"].delete_many({
        "username": {"$in": [AUTH_TEACHER_USERNAME, "regression_second_teacher"]}
    })
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
        db["users"].insert_one({
            "username": AUTH_TEACHER_USERNAME,
            "role": "teacher",
            "is_active": True,
        })
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

        expired = make_token("expired_student", "student", expires_in_hours=-1)
        status, _ = request(
            "GET",
            5005,
            "/api/module05/user-role",
            expired,
        )
        expect(status == 401, "expired JWT is rejected")

        status, _ = public_request(
            "POST",
            5001,
            "/api/module01/register",
            {
                "username": AUTH_TEACHER_USERNAME,
                "password": "Teacher123",
                "role": "teacher",
            },
        )
        expect(status == 409, "duplicate registration still returns HTTP 409")

        status, _ = public_request(
            "POST",
            5001,
            "/api/module01/register",
            {
                "username": "regression_second_teacher",
                "password": "Teacher123",
                "role": "teacher",
            },
        )
        expect(status == 403, "public teacher role escalation is blocked")

        response = requests.post(
            (
                f"{SINGLE_PROCESS_BASE_URL}/api/logs/write"
                if SINGLE_PROCESS_BASE_URL
                else f"{BASE_URL}:5000/api/logs/write"
            ),
            json={
                "module": "Module_01_Auth",
                "level": "INFO",
                "user_id": "attacker",
                "exam_id": EXAM_ID,
                "action": "forged_log",
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            },
            timeout=20,
        )
        expect(response.status_code == 401, "logging gateway rejects forged writes")

        wrong_state_requests = [
            (5010, "/api/module10/tab-switch", {"exam_id": EXAM_ID}),
            (
                5011,
                "/api/module11/clipboard-event",
                {"exam_id": EXAM_ID, "event_type": "paste"},
            ),
            (
                5012,
                "/api/module12/log-activity",
                {"exam_id": EXAM_ID, "action": "right_click_attempt"},
            ),
            (
                5015,
                "/api/module15/log-behavior",
                {"exam_id": EXAM_ID, "event_type": "idle", "value": 10},
            ),
        ]
        for port, path, body in wrong_state_requests:
            status, _ = request("POST", port, path, student_1, body)
            expect(status == 409, f"{path} rejects events outside IN_PROGRESS")

        status, _ = request(
            "GET",
            5017,
            f"/api/module17/risk-score/{USER_IDS[1]}/{EXAM_ID}",
            student_1,
        )
        expect(status == 403, "student cannot calculate risk scores")

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

        status, _ = request(
            "POST",
            5008,
            "/api/module08/start-timer",
            student_1,
            {"exam_id": EXAM_ID},
        )
        expect(status == 200, "activated student can start a timer")

        status, _ = request(
            "GET",
            5006,
            f"/api/module06/questions/{EXAM_ID}",
            student_2,
        )
        expect(
            status == 403,
            "student cannot read questions before starting their own timer",
        )

        status, _ = request(
            "POST",
            5008,
            "/api/module08/start-timer",
            student_2,
            {"exam_id": EXAM_ID},
        )
        expect(status == 200, "second activated student can start a timer")

        active_state_requests = [
            (5010, "/api/module10/tab-switch", {"exam_id": EXAM_ID}),
            (
                5011,
                "/api/module11/clipboard-event",
                {"exam_id": EXAM_ID, "event_type": "paste"},
            ),
            (
                5012,
                "/api/module12/log-activity",
                {"exam_id": EXAM_ID, "action": "right_click_attempt"},
            ),
            (
                5015,
                "/api/module15/log-behavior",
                {"exam_id": EXAM_ID, "event_type": "idle", "value": 301},
            ),
        ]
        for port, path, body in active_state_requests:
            status, _ = request("POST", port, path, student_1, body)
            expect(status == 200, f"{path} accepts events during IN_PROGRESS")

        status, _ = request(
            "POST",
            5012,
            "/api/module12/log-activity",
            student_1,
            {"exam_id": EXAM_ID, "action": "invented_action"},
        )
        expect(status == 400, "activity logging rejects unknown action names")

        status, _ = request(
            "POST",
            5015,
            "/api/module15/analyze",
            student_1,
            {"user_id": USER_IDS[1], "exam_id": EXAM_ID},
        )
        expect(status == 403, "student cannot run behavioral analysis")

        status, payload = request(
            "POST",
            5015,
            "/api/module15/analyze",
            teacher,
            {"user_id": USER_IDS[1], "exam_id": EXAM_ID},
        )
        expect(
            status == 200 and response_data(payload).get("flagged") is True,
            "teacher can detect a behavioral anomaly",
        )

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
        expect(
            db["exams"].find_one({"exam_id": EXAM_ID}).get("state") == "COMPLETED",
            "risk dashboard completes the exam state machine",
        )

        status, _ = request(
            "POST",
            5002,
            "/api/module02/invalidate-session",
            student_2,
            {"reason": "regression test"},
        )
        expect(status == 200, "session can be invalidated")

        status, _ = request(
            "GET",
            5005,
            "/api/module05/user-role",
            student_2,
        )
        expect(status == 401, "invalidated JWT is rejected by another module")

        old_session = make_token(
            "regression_multi_session",
            "student",
            session_id="old_session",
        )
        new_session = make_token(
            "regression_multi_session",
            "student",
            session_id="new_session",
        )
        status, payload = request(
            "POST",
            5014,
            "/api/module14/register-session",
            old_session,
            {"exam_id": EXAM_ID},
        )
        expect(
            status == 200
            and response_data(payload).get("multi_session_detected") is False,
            "first session is registered without a multi-session alert",
        )

        status, payload = request(
            "POST",
            5014,
            "/api/module14/register-session",
            new_session,
            {"exam_id": EXAM_ID},
        )
        expect(
            status == 200
            and response_data(payload).get("multi_session_detected") is True,
            "second distinct session terminates the previous session",
        )

        status, payload = request(
            "GET",
            5014,
            "/api/module14/check-session",
            new_session,
        )
        sessions = response_data(payload).get("sessions", [])
        expect(
            status == 200
            and sessions
            and all("token" not in session for session in sessions),
            "session status never exposes stored JWTs",
        )

        status, _ = request(
            "GET",
            5005,
            "/api/module05/user-role",
            old_session,
        )
        expect(status == 401, "terminated multi-session JWT is globally rejected")
    finally:
        cleanup(db)


if __name__ == "__main__":
    main()
