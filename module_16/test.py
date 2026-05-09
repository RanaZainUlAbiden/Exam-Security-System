# module_16/test_module16.py
# Run this to test all endpoints without needing other modules
# Usage: python test_module16.py

import sys
import os
import jwt
import datetime
import requests
import json
from pymongo import MongoClient

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

BASE_URL   = "http://localhost:5016"
MONGO_URI  = "mongodb://localhost:27017/"
DB_NAME    = "exam_security"

# Must match shared/jwt_helper.py
JWT_SECRET    = "exam_security_UET_2024_secret_key"
JWT_ALGORITHM = "HS256"

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def make_jwt(role: str, user_id: str, expired: bool = False) -> str:
    exp = datetime.datetime.utcnow() + (
        datetime.timedelta(seconds=-10) if expired
        else datetime.timedelta(hours=2)
    )
    payload = {
        "user_id":               user_id,
        "username":              f"test_{role}",
        "role":                  role,
        "session_id":            "test_session_001",
        "device_fingerprint_hash": "abc123",
        "exp":                   exp
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def print_result(test_name: str, passed: bool, response=None, note: str = ""):
    icon = "✅" if passed else "❌"
    print(f"\n{icon}  {test_name}")
    if note:
        print(f"    Note: {note}")
    if response is not None:
        try:
            print(f"    Status: {response.status_code}")
            data = response.json()
            print(f"    Body:   {json.dumps(data, indent=6)[:400]}")
        except Exception:
            print(f"    Body:   {response.text[:200]}")


# ─── SEED TEST DATA ───────────────────────────────────────────────────────────

def seed_test_data():
    """
    Insert fake exam + student responses into MongoDB so the module has
    something to analyze. Run once before tests.
    """
    client = MongoClient(MONGO_URI)
    db     = client[DB_NAME]

    # Clean up previous test data
    db["exams"].delete_many({"exam_id": "exam_test_001"})
    db["responses"].delete_many({"exam_id": "exam_test_001"})
    db["similarity_results"].delete_many({"exam_id": "exam_test_001"})

    # Insert a test exam
    db["exams"].insert_one({
        "exam_id":   "exam_test_001",
        "title":     "IS Lab Test Exam",
        "status":    "COMPLETED",
        "created_at": datetime.datetime.utcnow().isoformat()
    })

    # Insert student answers
    # student_001 and student_002 have nearly identical answers → should be flagged
    # student_003 has a unique answer → should NOT be flagged
    responses = [
        # Q1 — student_001 and student_002 copied from each other
        {
            "exam_id":    "exam_test_001",
            "question_id": "q1",
            "user_id":    "student_001",
            "answer_text": "TCP uses a three-way handshake for connection establishment. SYN, SYN-ACK, and ACK packets are exchanged between client and server.",
            "submitted_at": datetime.datetime.utcnow().isoformat()
        },
        {
            "exam_id":    "exam_test_001",
            "question_id": "q1",
            "user_id":    "student_002",
            "answer_text": "TCP uses a three-way handshake to establish connections. SYN, SYN-ACK, and ACK are the packets exchanged between client and server.",
            "submitted_at": datetime.datetime.utcnow().isoformat()
        },
        {
            "exam_id":    "exam_test_001",
            "question_id": "q1",
            "user_id":    "student_003",
            "answer_text": "Transmission Control Protocol ensures reliable delivery using acknowledgement numbers and sequence tracking over IP networks.",
            "submitted_at": datetime.datetime.utcnow().isoformat()
        },

        # Q2 — all three have different answers
        {
            "exam_id":    "exam_test_001",
            "question_id": "q2",
            "user_id":    "student_001",
            "answer_text": "A firewall filters network traffic based on predefined rules to block unauthorized access.",
            "submitted_at": datetime.datetime.utcnow().isoformat()
        },
        {
            "exam_id":    "exam_test_001",
            "question_id": "q2",
            "user_id":    "student_002",
            "answer_text": "Encryption converts plaintext into ciphertext using keys so only authorized parties can read the data.",
            "submitted_at": datetime.datetime.utcnow().isoformat()
        },
        {
            "exam_id":    "exam_test_001",
            "question_id": "q2",
            "user_id":    "student_003",
            "answer_text": "Intrusion detection systems monitor network traffic for suspicious patterns and raise alerts.",
            "submitted_at": datetime.datetime.utcnow().isoformat()
        },
    ]
    db["responses"].insert_many(responses)
    print("✅  Test data seeded into MongoDB (exam_test_001)")
    client.close()


# ─── TESTS ────────────────────────────────────────────────────────────────────

def run_tests():
    teacher_token  = make_jwt("teacher",  "teacher_001")
    student_token  = make_jwt("student",  "student_001")
    expired_token  = make_jwt("teacher",  "teacher_001", expired=True)

    print("\n" + "="*60)
    print("  MODULE 16 — ANSWER SIMILARITY DETECTION — TEST SUITE")
    print("="*60)

    # ── TEST 1: Health check ──────────────────────────────────────
    r = requests.get(f"{BASE_URL}/api/module16/health")
    print_result("Health check returns 200",
                 r.status_code == 200 and r.json().get("status") == "healthy",
                 r)

    # ── TEST 2: JWT required — no token ──────────────────────────
    r = requests.post(f"{BASE_URL}/api/module16/check-similarity",
                      json={"exam_id": "exam_test_001"})
    print_result("No token → 401",
                 r.status_code == 401, r)

    # ── TEST 3: Expired JWT → 401 ─────────────────────────────────
    r = requests.post(f"{BASE_URL}/api/module16/check-similarity",
                      headers=headers(expired_token),
                      json={"exam_id": "exam_test_001"})
    print_result("Expired token → 401",
                 r.status_code == 401, r)

    # ── TEST 4: Student cannot trigger analysis → 403 ─────────────
    r = requests.post(f"{BASE_URL}/api/module16/check-similarity",
                      headers=headers(student_token),
                      json={"exam_id": "exam_test_001"})
    print_result("Student role → 403 on check-similarity",
                 r.status_code == 403, r)

    # ── TEST 5: Missing exam_id → 400 ────────────────────────────
    r = requests.post(f"{BASE_URL}/api/module16/check-similarity",
                      headers=headers(teacher_token),
                      json={})
    print_result("Missing exam_id → 400",
                 r.status_code == 400, r)

    # ── TEST 6: NoSQL injection attempt → 400 ────────────────────
    r = requests.post(f"{BASE_URL}/api/module16/check-similarity",
                      headers=headers(teacher_token),
                      json={"exam_id": {"$gt": ""}})
    print_result("NoSQL injection in exam_id → 400",
                 r.status_code == 400, r,
                 note="exam_id must be a string, operator objects rejected")

    # ── TEST 7: Special chars in exam_id → 400 ───────────────────
    r = requests.post(f"{BASE_URL}/api/module16/check-similarity",
                      headers=headers(teacher_token),
                      json={"exam_id": "exam'; DROP TABLE exams;--"})
    print_result("Special chars in exam_id → 400",
                 r.status_code == 400, r)

    # ── TEST 8: Non-existent exam → 404 ──────────────────────────
    r = requests.post(f"{BASE_URL}/api/module16/check-similarity",
                      headers=headers(teacher_token),
                      json={"exam_id": "exam_does_not_exist"})
    print_result("Non-existent exam → 404",
                 r.status_code == 404, r)

    # ── TEST 9: Valid analysis — should flag student_001 and student_002
    r = requests.post(f"{BASE_URL}/api/module16/check-similarity",
                      headers=headers(teacher_token),
                      json={"exam_id": "exam_test_001"})
    data = r.json()
    pairs = data.get("data", {}).get("pairs", [])
    flagged = data.get("data", {}).get("flagged_pairs", 0)
    print_result("Valid analysis — student_001 & student_002 flagged",
                 r.status_code == 200 and flagged >= 1, r,
                 note="Q1 answers are nearly identical — should score ≥ 0.75")

    # ── TEST 10: Risk data for flagged student ────────────────────
    r = requests.get(f"{BASE_URL}/api/module16/risk-data",
                     headers=headers(teacher_token),
                     params={"user_id": "student_001", "exam_id": "exam_test_001"})
    score = r.json().get("data", {}).get("data", [{}])[0].get("value", 0)
    print_result("Risk data for flagged student has score > 0",
                 r.status_code == 200 and score > 0, r)

    # ── TEST 11: Risk data for clean student ──────────────────────
    r = requests.get(f"{BASE_URL}/api/module16/risk-data",
                     headers=headers(teacher_token),
                     params={"user_id": "student_003", "exam_id": "exam_test_001"})
    score = r.json().get("data", {}).get("data", [{}])[0].get("value", 0)
    print_result("Risk data for clean student has score = 0",
                 r.status_code == 200 and score == 0.0, r,
                 note="student_003 had unique answers, should not be flagged")

    # ── TEST 12: Risk data missing params → 400 ───────────────────
    r = requests.get(f"{BASE_URL}/api/module16/risk-data",
                     headers=headers(teacher_token))
    print_result("risk-data missing params → 400",
                 r.status_code == 400, r)

    # ── TEST 13: Report endpoint — integrity verified ─────────────
    r = requests.get(f"{BASE_URL}/api/module16/report",
                     headers=headers(teacher_token),
                     params={"exam_id": "exam_test_001"})
    integrity_ok = r.json().get("data", {}).get("integrity_verified", False)
    print_result("Report integrity_verified = true",
                 r.status_code == 200 and integrity_ok, r)

    # ── TEST 14: Rate limiting (6 rapid calls, 6th should be 429) ─
    print("\n⏳  Testing rate limiter (sending 6 rapid requests)...")
    rate_token = make_jwt("teacher", "teacher_rate_test")
    last_status = None
    for i in range(6):
        r = requests.post(f"{BASE_URL}/api/module16/check-similarity",
                          headers=headers(rate_token),
                          json={"exam_id": "exam_test_001"})
        last_status = r.status_code
    print_result("6th rapid request → 429 rate limited",
                 last_status == 429, r,
                 note="Max 5 calls/min per teacher")

    print("\n" + "="*60)
    print("  TESTS COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\nSeeding test data into MongoDB...")
    try:
        seed_test_data()
    except Exception as e:
        print(f"❌  MongoDB seed failed: {e}")
        print("    Make sure MongoDB is running: mongod")
        sys.exit(1)

    print("\nRunning tests against http://localhost:5016 ...")
    print("Make sure module is running: python app.py\n")

    try:
        run_tests()
    except requests.exceptions.ConnectionError:
        print("❌  Cannot connect to localhost:5016")
        print("    Start the module first: python app.py")