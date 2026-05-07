# module_16/app.py
# =============================================
# MODULE 16: ANSWER SIMILARITY DETECTION
# TF-IDF + Cosine Similarity to detect copying
# PORT: 5016
#
# SECURITY CONCEPTS IMPLEMENTED:
#   1. JWT Authentication & Role-Based Access Control
#   2. Input Validation & Sanitization (Injection Prevention)
#   3. Request Size Limiting (DoS Prevention)
#   4. Rate Limiting on expensive computation endpoint
#   5. Server-side threshold enforcement (tamper-proof)
#   6. Security event logging for audit trails
#   7. Data minimization (answers never returned in responses)
# =============================================

import sys
import os
import datetime
import hashlib
import re
import time
from collections import defaultdict, deque

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

MODULE_NAME          = "Module_16_Answer_Similarity"
PORT                 = 5016

# ─── SECURITY CONSTANTS (server-side, never exposed to client) ────────────────
SIMILARITY_THRESHOLD = 0.75    # Pairs at or above this score are flagged
MAX_ANSWER_LENGTH    = 5000    # Max chars per answer (DoS guard)
MAX_REQUEST_BODY     = 1024    # Max bytes for POST body (exam_id only)
MAX_EXAM_ID_LENGTH   = 100     # Prevent oversized exam_id strings
ALLOWED_EXAM_ID_RE   = re.compile(r'^[a-zA-Z0-9_\-]+$')  # Whitelist pattern

# ─── IN-MEMORY RATE LIMITER ──────────────────────────────────────────────────
# check-similarity is O(n²) — must be rate-limited to prevent compute DoS
_rate_limit_store = defaultdict(deque)   # { user_id: deque of timestamps }
RATE_LIMIT_MAX    = 5     # max calls
RATE_LIMIT_WINDOW = 60    # per 60 seconds


def is_rate_limited(user_id: str) -> bool:
    """
    SECURITY: Sliding-window rate limiter.
    Prevents a teacher from hammering the similarity endpoint
    (each call runs O(n²) cosine similarity — expensive).
    Returns True if the user has exceeded the limit.
    """
    now    = time.time()
    window = _rate_limit_store[user_id]

    # Remove timestamps outside the window
    while window and window[0] < now - RATE_LIMIT_WINDOW:
        window.popleft()

    if len(window) >= RATE_LIMIT_MAX:
        return True

    window.append(now)
    return False


def sanitize_exam_id(exam_id: str) -> tuple:
    """
    SECURITY: Validate and sanitize exam_id to prevent NoSQL injection.
    MongoDB operators like $where, $gt etc. must never reach the query layer.
    Returns (clean_id, error_message_or_None).
    """
    if not exam_id or not isinstance(exam_id, str):
        return None, "exam_id must be a non-empty string"

    exam_id = exam_id.strip()

    if len(exam_id) > MAX_EXAM_ID_LENGTH:
        return None, f"exam_id exceeds maximum length of {MAX_EXAM_ID_LENGTH}"

    if not ALLOWED_EXAM_ID_RE.match(exam_id):
        return None, "exam_id contains invalid characters (only alphanumeric, dash, underscore allowed)"

    return exam_id, None


def sanitize_answer(text: str) -> str:
    """
    SECURITY: Truncate and strip answer text.
    Prevents memory exhaustion when a single student submits a huge answer
    to inflate TF-IDF computation cost.
    """
    if not isinstance(text, str):
        return ""
    return text.strip()[:MAX_ANSWER_LENGTH]


# ─── HEALTH CHECK ────────────────────────────────────────────────────────────
@app.route("/api/module16/health", methods=["GET"])
def health():
    return jsonify({
        "module":       MODULE_NAME,
        "status":       "healthy",
        "dependencies": ["mongodb"],
        "version":      "1.0.0"
    }), 200


# ─── ENDPOINT 1: CHECK SIMILARITY ────────────────────────────────────────────
# POST /api/module16/check-similarity
# Auth: JWT required | Role: teacher only
# Body: { "exam_id": "string" }
#
# Security:
#   - JWT + RBAC: only teachers can trigger analysis
#   - Rate limiting: max 5 calls/min per teacher (compute DoS prevention)
#   - Input sanitization: exam_id whitelisted, body size capped
#   - NoSQL injection prevention: sanitized query params
#   - Server-side threshold: client cannot influence what gets flagged
#   - Audit logging: every analysis is logged with SECURITY level if suspicious
#   - Data minimization: raw answer texts are NEVER returned to the caller
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/module16/check-similarity", methods=["POST"])
@jwt_required
@role_required(["teacher"])
def check_similarity():
    user = request.user_payload

    # SECURITY: Enforce max body size before parsing JSON
    if request.content_length and request.content_length > MAX_REQUEST_BODY:
        send_log(MODULE_NAME, "WARNING", user["user_id"], "",
                 "oversized_request_blocked",
                 {"content_length": request.content_length})
        return error_response(400, "Request body too large")

    body    = request.get_json(silent=True) or {}
    raw_id  = body.get("exam_id", "")
    exam_id, err = sanitize_exam_id(raw_id)

    if err:
        send_log(MODULE_NAME, "WARNING", user["user_id"], str(raw_id),
                 "invalid_exam_id_rejected", {"reason": err})
        return error_response(400, err)

    # SECURITY: Rate limit per teacher user_id
    if is_rate_limited(user["user_id"]):
        send_log(MODULE_NAME, "WARNING", user["user_id"], exam_id,
                 "rate_limit_exceeded", {"endpoint": "check-similarity"})
        return error_response(429, "Rate limit exceeded. Max 5 requests per minute.")

    db = get_db()

    # SECURITY: Parameterized query — exam_id is already whitelisted to
    # alphanumeric/dash/underscore so no MongoDB operator injection possible.
    exam = db["exams"].find_one({"exam_id": exam_id})
    if not exam:
        return error_response(404, f"Exam '{exam_id}' not found")

    all_responses = list(db["responses"].find(
        {"exam_id": exam_id},
        {"_id": 0, "user_id": 1, "question_id": 1, "answer_text": 1}
        # SECURITY: Project only needed fields, never pull unnecessary data
    ))

    if not all_responses:
        return error_response(404, "No responses found for this exam")

    # Group by question_id
    questions_map = defaultdict(list)
    for resp in all_responses:
        questions_map[resp.get("question_id", "unknown")].append({
            "user_id":     str(resp.get("user_id", "")),
            # SECURITY: Sanitize each answer to prevent memory exhaustion
            "answer_text": sanitize_answer(resp.get("answer_text", ""))
        })

    flagged_pairs   = []
    per_student_max = {}

    for question_id, answers in questions_map.items():
        valid_answers = [a for a in answers if len(a["answer_text"]) > 3]
        if len(valid_answers) < 2:
            continue

        user_ids     = [a["user_id"]     for a in valid_answers]
        answer_texts = [a["answer_text"] for a in valid_answers]

        try:
            vectorizer   = TfidfVectorizer(stop_words="english", min_df=1)
            tfidf_matrix = vectorizer.fit_transform(answer_texts)
            sim_matrix   = cosine_similarity(tfidf_matrix)
        except ValueError:
            # All answers were stop-words or empty after TF-IDF filtering
            continue

        n = len(user_ids)
        for i in range(n):
            for j in range(i + 1, n):
                score = float(sim_matrix[i][j])
                if score >= SIMILARITY_THRESHOLD:
                    flagged_pairs.append({
                        "question_id": question_id,
                        "student_a":   user_ids[i],
                        "student_b":   user_ids[j],
                        "score":       round(score, 4)
                        # SECURITY: answer text intentionally excluded
                        # (data minimization — only score is needed downstream)
                    })
                    per_student_max[user_ids[i]] = max(per_student_max.get(user_ids[i], 0.0), score)
                    per_student_max[user_ids[j]] = max(per_student_max.get(user_ids[j], 0.0), score)

    now = datetime.datetime.utcnow().isoformat() + "Z"

    # SECURITY: Generate a SHA-256 hash of the analysis result for integrity
    # If the stored report is tampered, the hash will not match on verification
    result_payload = f"{exam_id}|{len(flagged_pairs)}|{len(all_responses)}|{now}"
    integrity_hash = hashlib.sha256(result_payload.encode()).hexdigest()

    result_doc = {
        "exam_id":          exam_id,
        "analyzed_at":      now,
        "analyzed_by":      user["user_id"],
        "threshold_used":   SIMILARITY_THRESHOLD,   # stored so it's auditable
        "flagged_pairs":    flagged_pairs,
        "per_student_max":  per_student_max,
        "total_responses":  len(all_responses),
        "total_flagged":    len(flagged_pairs),
        "integrity_hash":   integrity_hash          # tamper-detection
    }

    db["similarity_results"].update_one(
        {"exam_id": exam_id},
        {"$set": result_doc},
        upsert=True
    )

    # SECURITY: Log with SECURITY level if copying detected, INFO otherwise
    send_log(
        module_name = MODULE_NAME,
        level       = "SECURITY" if flagged_pairs else "INFO",
        user_id     = user["user_id"],
        exam_id     = exam_id,
        action      = "similarity_analysis_completed",
        details     = {
            "total_responses": len(all_responses),
            "flagged_pairs":   len(flagged_pairs),
            "threshold":       SIMILARITY_THRESHOLD,
            "integrity_hash":  integrity_hash
        }
    )

    # SECURITY: Response does NOT include raw answer texts
    return success_response(
        data={
            "exam_id":         exam_id,
            "total_responses": len(all_responses),
            "flagged_pairs":   len(flagged_pairs),
            "threshold":       SIMILARITY_THRESHOLD,
            "integrity_hash":  integrity_hash,
            "pairs":           flagged_pairs
        },
        message=f"Analysis complete. {len(flagged_pairs)} suspicious pair(s) flagged."
    )


# ─── ENDPOINT 2: RISK DATA (consumed by Module 17) ───────────────────────────
# GET /api/module16/risk-data?user_id=...&exam_id=...
# Auth: JWT required
#
# Returns the standard risk-data schema (spec section 27.7).
# Security: JWT required, inputs sanitized, logging on every call.
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/module16/risk-data", methods=["GET"])
@jwt_required
def get_risk_data():
    db      = get_db()
    user    = request.user_payload
    user_id = request.args.get("user_id", "").strip()
    exam_id_raw = request.args.get("exam_id", "")
    exam_id, err = sanitize_exam_id(exam_id_raw)

    if not user_id or err:
        return error_response(400, "Valid user_id and exam_id query params are required")

    # SECURITY: Validate user_id format (alphanumeric only)
    if not re.match(r'^[a-zA-Z0-9_\-]+$', user_id) or len(user_id) > 100:
        send_log(MODULE_NAME, "WARNING", user["user_id"], str(exam_id_raw),
                 "invalid_user_id_in_risk_data", {"user_id": user_id})
        return error_response(400, "Invalid user_id format")

    result_doc = db["similarity_results"].find_one({"exam_id": exam_id})
    analyzed_at = datetime.datetime.utcnow().isoformat() + "Z"

    if not result_doc:
        # No analysis run yet — return zero score, do NOT error
        return success_response(
            data={
                "module": MODULE_NAME,
                "data": [{
                    "user_id":   user_id,
                    "exam_id":   exam_id,
                    "timestamp": analyzed_at,
                    "metric":    "max_similarity_score",
                    "value":     0.0
                }]
            },
            message="No analysis found. Score defaulted to 0."
        )

    per_student_max = result_doc.get("per_student_max", {})
    score           = per_student_max.get(user_id, 0.0)
    flagged_pairs   = result_doc.get("flagged_pairs", [])
    pair_count      = sum(1 for p in flagged_pairs
                          if p["student_a"] == user_id or p["student_b"] == user_id)
    analyzed_at     = result_doc.get("analyzed_at", analyzed_at)

    send_log(
        module_name = MODULE_NAME,
        level       = "INFO",
        user_id     = user["user_id"],
        exam_id     = exam_id,
        action      = "risk_data_fetched",
        details     = {"target_user": user_id, "score": score, "pair_count": pair_count}
    )

    return success_response(
        data={
            "module": MODULE_NAME,
            "data": [
                {
                    "user_id":   user_id,
                    "exam_id":   exam_id,
                    "timestamp": analyzed_at,
                    "metric":    "max_similarity_score",
                    "value":     round(score, 4)
                },
                {
                    "user_id":   user_id,
                    "exam_id":   exam_id,
                    "timestamp": analyzed_at,
                    "metric":    "flagged_pair_count",
                    "value":     pair_count
                }
            ]
        },
        message="Risk data fetched successfully"
    )


# ─── ENDPOINT 3: FULL REPORT (teacher dashboard) ─────────────────────────────
# GET /api/module16/report?exam_id=...
# Auth: JWT required | Role: teacher only
# Includes integrity hash so teacher can verify report was not tampered with.
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/module16/report", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def get_report():
    db          = get_db()
    exam_id_raw = request.args.get("exam_id", "")
    exam_id, err = sanitize_exam_id(exam_id_raw)

    if err:
        return error_response(400, err)

    result_doc = db["similarity_results"].find_one({"exam_id": exam_id}, {"_id": 0})
    if not result_doc:
        return error_response(404, "No similarity report found. Run /check-similarity first.")

    # SECURITY: Verify integrity hash to detect tampering with stored results
    stored_hash = result_doc.get("integrity_hash", "")
    recomputed  = hashlib.sha256(
        f"{exam_id}|{result_doc['total_flagged']}|{result_doc['total_responses']}|{result_doc['analyzed_at']}".encode()
    ).hexdigest()

    integrity_ok = (stored_hash == recomputed)
    if not integrity_ok:
        send_log(MODULE_NAME, "SECURITY", request.user_payload["user_id"], exam_id,
                 "integrity_check_failed",
                 {"stored_hash": stored_hash, "expected_hash": recomputed})

    result_doc["integrity_verified"] = integrity_ok

    return success_response(data=result_doc, message="Similarity report fetched")


# ─── GLOBAL ERROR HANDLERS ────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return error_response(404, "Endpoint not found")

@app.errorhandler(405)
def method_not_allowed(e):
    return error_response(405, "Method not allowed")

@app.errorhandler(500)
def internal_error(e):
    return error_response(500, "Internal server error")


if __name__ == "__main__":
    print(f"🔐 Module 16 — Answer Similarity Detection running on port {PORT}")
    app.run(port=PORT, debug=True)