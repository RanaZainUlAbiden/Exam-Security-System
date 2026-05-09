import sys
import json
import time
import argparse
import datetime
import requests
import jwt as pyjwt  

BASE_URL      = "http://localhost:5007"
JWT_SECRET    = "exam_security_UET_2024_secret_key"
JWT_ALGORITHM = "HS256"
TEST_EXAM_ID  = "exam_test_module07"

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

pass_count = 0
fail_count = 0


def _make_token(user_id="student_001", role="student",
                session_id="sess_abc", expired=False):
    delta = datetime.timedelta(seconds=-1) if expired else datetime.timedelta(hours=24)
    payload = {
        "user_id":                 user_id,
        "username":                user_id,
        "role":                    role,
        "session_id":              session_id,
        "device_fingerprint_hash": "test_hash",
        "exp":                     datetime.datetime.utcnow() + delta,
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def check(name: str, condition: bool, detail: str = ""):
    global pass_count, fail_count
    if condition:
        print(f"  {GREEN}✅ PASS{RESET}  {name}")
        pass_count += 1
    else:
        print(f"  {RED}❌ FAIL{RESET}  {name}" + (f"  →  {detail}" if detail else ""))
        fail_count += 1


def section(title: str):
    print(f"\n{CYAN}{BOLD}{'─'*55}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{BOLD}{'─'*55}{RESET}")



def test_health():
    section("1. Health Check")
    try:
        r = requests.get(f"{BASE_URL}/api/module07/health", timeout=3)
        check("HTTP 200", r.status_code == 200, str(r.status_code))
        data = r.json()
        check("module name present", "module" in data)
        check("status present", data.get("status") in ("healthy", "degraded"))
        check("dependencies listed", "mongodb" in data.get("dependencies", []))
        print(f"    → Status: {data.get('status')}")
    except Exception as e:
        check("module reachable", False, str(e))


def test_jwt_validation():
    section("2. JWT Security Validation")

    r = requests.get(f"{BASE_URL}/api/module07/randomized-questions/{TEST_EXAM_ID}")
    check("No token → 401", r.status_code == 401, str(r.status_code))
    check("Error format correct", r.json().get("status") == "error")

    expired = _make_token(expired=True)
    r = requests.get(
        f"{BASE_URL}/api/module07/randomized-questions/{TEST_EXAM_ID}",
        headers=_headers(expired)
    )
    check("Expired token → 401", r.status_code == 401, str(r.status_code))

    bad_payload = {
        "user_id": "hacker", "username": "hacker", "role": "student",
        "session_id": "x", "device_fingerprint_hash": "y",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    
    tampered = pyjwt.encode(bad_payload, "wrong_secret", algorithm="HS256")
    r = requests.get(
        f"{BASE_URL}/api/module07/randomized-questions/{TEST_EXAM_ID}",
        headers=_headers(tampered)
    )
    check("Tampered token → 401", r.status_code == 401, str(r.status_code))

    r = requests.get(
        f"{BASE_URL}/api/module07/randomized-questions/{TEST_EXAM_ID}",
        headers={"Authorization": "NotBearer abc"}
    )
    check("Malformed header → 401", r.status_code == 401, str(r.status_code))


def test_role_enforcement():
    section("3. Role Enforcement")

    teacher_token = _make_token(user_id="teacher_001", role="teacher")
    r = requests.get(
        f"{BASE_URL}/api/module07/randomized-questions/{TEST_EXAM_ID}",
        headers=_headers(teacher_token)
    )
    check("Teacher cannot fetch shuffled questions → 403", r.status_code == 403,
          str(r.status_code))

    student_token = _make_token()
    r = requests.get(
        f"{BASE_URL}/api/module07/shuffle-mapping/{TEST_EXAM_ID}",
        headers=_headers(student_token)
    )
    check("Student cannot see shuffle mapping → 403", r.status_code == 403,
          str(r.status_code))

    r = requests.get(
        f"{BASE_URL}/api/module07/stats/{TEST_EXAM_ID}",
        headers=_headers(student_token)
    )
    check("Student cannot see stats → 403", r.status_code == 403, str(r.status_code))


def setup_exam_in_db():
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/")
        db     = client["exam_security"]

        db["exams"].update_one(
            {"exam_id": TEST_EXAM_ID},
            {"$set": {
                "exam_id": TEST_EXAM_ID,
                "state":   "IN_PROGRESS",
                "title":   "Module 07 Test Exam",
            }},
            upsert=True
        )
        return True, db
    except Exception as e:
        print(f"  {YELLOW}⚠️  Could not connect to MongoDB: {e}{RESET}")
        print(f"  {YELLOW}   Make sure MongoDB is running on localhost:27017{RESET}")
        return False, None


def test_exam_state_guard():
    section("4. Exam State Guard (HTTP 409)")

    token = _make_token()

    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/")
        db     = client["exam_security"]
        db["exams"].update_one(
            {"exam_id": TEST_EXAM_ID},
            {"$set": {"exam_id": TEST_EXAM_ID, "state": "NOT_STARTED"}},
            upsert=True
        )
        r = requests.get(
            f"{BASE_URL}/api/module07/randomized-questions/{TEST_EXAM_ID}",
            headers=_headers(token)
        )
        check("Wrong state (NOT_STARTED) → 409", r.status_code == 409, str(r.status_code))

        r = requests.get(
            f"{BASE_URL}/api/module07/randomized-questions/nonexistent_exam_xyz",
            headers=_headers(token)
        )
        check("Non-existent exam → 404", r.status_code == 404, str(r.status_code))

    except ImportError:
        print(f"  {YELLOW}⚠️  pymongo not importable in test env — skipping state guard test{RESET}")


def test_seed_and_fetch():
    section("5–8. Seed Questions + Randomization Tests")

    db_ok, db = setup_exam_in_db()
    if not db_ok:
        print(f"  {YELLOW}⚠️  Skipping — MongoDB not reachable{RESET}")
        return

    teacher_token  = _make_token(user_id="teacher_001", role="teacher")
    student1_token = _make_token(user_id="student_001", role="student", session_id="sess_s1")
    student2_token = _make_token(user_id="student_002", role="student", session_id="sess_s2")

    db["exams"].update_one(
        {"exam_id": TEST_EXAM_ID},
        {"$set": {"state": "IN_PROGRESS"}},
        upsert=True
    )

    r = requests.post(
        f"{BASE_URL}/api/module07/seed-questions",
        headers=_headers(teacher_token),
        json={"exam_id": TEST_EXAM_ID}
    )
    check("Teacher seeds questions → 200", r.status_code == 200, r.text[:100])
    if r.status_code == 200:
        inserted = r.json()["data"]["questions_inserted"]
        print(f"    → Inserted {inserted} questions")

    r1 = requests.get(
        f"{BASE_URL}/api/module07/randomized-questions/{TEST_EXAM_ID}",
        headers=_headers(student1_token)
    )
    check("Student 1 gets questions → 200", r1.status_code == 200, r1.text[:150])

    if r1.status_code != 200:
        print(f"    {RED}Cannot continue tests — question fetch failed{RESET}")
        return

    qs1 = r1.json()["data"]["questions"]
    check("Response has questions list", isinstance(qs1, list) and len(qs1) > 0)
    check("Each question has shuffled_index", all("shuffled_index" in q for q in qs1))
    check("Each question has question_id",    all("question_id" in q for q in qs1))
    check("Each question has options",        all("options" in q for q in qs1))
    print(f"    → Student 1 order: {[q['question_id'] for q in qs1[:5]]} ...")

    r1b = requests.get(
        f"{BASE_URL}/api/module07/randomized-questions/{TEST_EXAM_ID}",
        headers=_headers(student1_token)
    )
    qs1b = r1b.json()["data"]["questions"]
    order1  = [q["question_id"] for q in qs1]
    order1b = [q["question_id"] for q in qs1b]
    check("Idempotency: same student same order on re-fetch", order1 == order1b,
          f"\n      First:  {order1}\n      Second: {order1b}")

    r2 = requests.get(
        f"{BASE_URL}/api/module07/randomized-questions/{TEST_EXAM_ID}",
        headers=_headers(student2_token)
    )
    check("Student 2 gets questions → 200", r2.status_code == 200)

    if r2.status_code == 200:
        qs2    = r2.json()["data"]["questions"]
        order2 = [q["question_id"] for q in qs2]
        check(
            "ANTI-COLLUSION: Student 1 & 2 have DIFFERENT question orders",
            order1 != order2,
            f"\n      S1: {order1}\n      S2: {order2}"
        )
        print(f"    → Student 2 order: {[q['question_id'] for q in qs2[:5]]} ...")

        q1_opts = [q["options"] for q in qs1]
        q2_opts = [q["options"] for q in qs2]
        opts_differ = any(o1 != o2 for o1, o2 in zip(q1_opts[:5], q2_opts[:5]))

        print(f"    → Options shuffled differently for at least one question: {opts_differ}")


def test_teacher_endpoints():
    section("9–11. Teacher Endpoints")

    teacher_token = _make_token(user_id="teacher_001", role="teacher")

    r = requests.get(
        f"{BASE_URL}/api/module07/shuffle-mapping/{TEST_EXAM_ID}",
        headers=_headers(teacher_token)
    )
    check("Teacher gets shuffle mapping → 200", r.status_code == 200, str(r.status_code))
    if r.status_code == 200:
        data = r.json()["data"]
        check("Mapping contains list", isinstance(data.get("mappings"), list))
        print(f"    → {data.get('total_maps')} student mappings found")

    r = requests.get(
        f"{BASE_URL}/api/module07/verify-seed/{TEST_EXAM_ID}"
        f"?user_id=student_001&session_id=sess_s1",
        headers=_headers(teacher_token)
    )
    check("Teacher verifies seed → 200", r.status_code == 200, str(r.status_code))
    if r.status_code == 200:
        data = r.json()["data"]
        check("seed_proof is 64-char hex", len(data.get("seed_proof", "")) == 64)
        print(f"    → Seed proof: {data.get('seed_proof', '')[:32]}...")

    r = requests.get(
        f"{BASE_URL}/api/module07/stats/{TEST_EXAM_ID}",
        headers=_headers(teacher_token)
    )
    check("Teacher gets stats → 200", r.status_code == 200, str(r.status_code))
    if r.status_code == 200:
        data = r.json()["data"]
        print(f"    → {data.get('students_randomized')} students randomized, "
              f"{data.get('total_questions')} questions")

    r = requests.get(
        f"{BASE_URL}/api/module07/verify-seed/{TEST_EXAM_ID}",
        headers=_headers(teacher_token)
    )
    check("verify-seed without user_id → 400", r.status_code == 400, str(r.status_code))



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Skip DB-dependent tests")
    args = parser.parse_args()

    print(f"\n{BOLD}{'='*55}{RESET}")
    print(f"{BOLD}  MODULE 07 — Question Randomization Test Suite{RESET}")
    print(f"{BOLD}{'='*55}{RESET}")
    print(f"  Target: {BASE_URL}")
    print(f"  Exam:   {TEST_EXAM_ID}")

    test_health()
    test_jwt_validation()
    test_role_enforcement()

    if not args.quick:
        test_exam_state_guard()
        test_seed_and_fetch()
        test_teacher_endpoints()
    else:
        print(f"\n{YELLOW}  (--quick mode: skipping DB tests){RESET}")

    total = pass_count + fail_count
    print(f"\n{BOLD}{'='*55}{RESET}")
    colour = GREEN if fail_count == 0 else RED
    print(f"{colour}{BOLD}  Results: {pass_count}/{total} passed | {fail_count} failed{RESET}")
    print(f"{BOLD}{'='*55}{RESET}\n")

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()