# Module 16 — Answer Similarity Detection

**Course:** Information Security Lab  
**Port:** `5016`  
**Tech Stack:** Python · Flask · MongoDB · scikit-learn (TF-IDF)

---

## 1. Security Concept

### What security problem does this module solve?
Online exams are vulnerable to **answer collusion** — students sharing answers with each other during or after an exam, then submitting identical or near-identical responses. Traditional plagiarism detection tools are not integrated into exam systems in real time. This module detects copying using mathematical text similarity, creating an automated anti-collusion layer.

### What attack is prevented?
| Attack | How it manifests | How this module stops it |
|---|---|---|
| Answer copying | Two students submit the same or paraphrased text | TF-IDF + cosine similarity flags pairs above 0.75 threshold |
| Threshold manipulation | Client tries to send a custom threshold to make their answers "pass" | Threshold is hardcoded server-side, never accepted from request body |
| NoSQL Injection | Attacker sends `{"exam_id": {"$gt": ""}}` to dump all exams | `exam_id` is whitelisted to alphanumeric/dash/underscore before any DB query |
| Compute DoS | Spamming the similarity endpoint crashes the server (O(n²) work) | Sliding-window rate limiter: max 5 calls per teacher per 60 seconds |
| Oversized payload DoS | Sending a 50MB request body to exhaust memory | Request body capped at 1024 bytes; individual answers capped at 5000 chars |
| Report tampering | Someone modifies flagged_pairs in MongoDB directly | SHA-256 integrity hash stored alongside report; `/report` endpoint re-computes and verifies |
| Unauthorized access | Student tries to trigger analysis or view full report | RBAC enforced via `@role_required(["teacher"])` on sensitive endpoints |
| Missing JWT | Any unauthenticated request | `@jwt_required` decorator returns HTTP 401 on every protected route |

### How is it implemented?
1. **TF-IDF Vectorization** — Converts each student's answer into a term-frequency/inverse-document-frequency vector, which captures word importance rather than just word count.  
2. **Cosine Similarity** — Measures the angle between two TF-IDF vectors. Score of 1.0 = identical content, 0.0 = completely different. Threshold 0.75 is aggressive enough to catch paraphrasing while avoiding false positives on short answers.  
3. **Per-question analysis** — Grouping by `question_id` ensures a student who happened to write the same phrase in one answer doesn't unfairly get flagged for a different question.  
4. **SHA-256 integrity hash** — After every analysis, a hash of `exam_id|flagged_count|total_responses|timestamp` is stored. The `/report` endpoint re-computes this and flags if it doesn't match — detecting any direct MongoDB tampering.  
5. **Server-side threshold** — `SIMILARITY_THRESHOLD = 0.75` is a Python constant, never read from the request. A malicious teacher cannot set it to 1.0 to clear their students.

---

## 2. API Endpoints

### Base URL
```
http://localhost:5016
```

### Authentication
All endpoints (except `/health`) require:
```
Authorization: Bearer <JWT_TOKEN>
```

---

### `GET /api/module16/health`
Returns module health status. No auth required.

**Response 200:**
```json
{
  "module": "Module_16_Answer_Similarity",
  "status": "healthy",
  "dependencies": ["mongodb"],
  "version": "1.0.0"
}
```

---

### `POST /api/module16/check-similarity`
Runs TF-IDF + cosine similarity on all student answers for an exam. Flags suspicious pairs.

**Auth:** JWT required | **Role:** `teacher` only  
**Rate limit:** 5 requests per minute per teacher

**Request Body:**
```json
{
  "exam_id": "exam_spring_2024_01"
}
```

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "exam_id": "exam_spring_2024_01",
    "total_responses": 45,
    "flagged_pairs": 3,
    "threshold": 0.75,
    "integrity_hash": "a3f9c2...",
    "pairs": [
      {
        "question_id": "q1",
        "student_a": "user_001",
        "student_b": "user_007",
        "score": 0.9231
      }
    ]
  },
  "message": "Analysis complete. 3 suspicious pair(s) flagged."
}
```

**Error Responses:**

| Code | Reason |
|---|---|
| 400 | Missing/invalid exam_id |
| 401 | Missing or expired JWT |
| 403 | Role is not teacher |
| 404 | Exam or responses not found |
| 429 | Rate limit exceeded |

---

### `GET /api/module16/risk-data?user_id=&exam_id=`
Returns per-student similarity data for Module 17 risk scoring.

**Auth:** JWT required  
**Query Params:** `user_id`, `exam_id`

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "module": "Module_16_Answer_Similarity",
    "data": [
      {
        "user_id": "user_001",
        "exam_id": "exam_spring_2024_01",
        "timestamp": "2024-05-08T10:30:00Z",
        "metric": "max_similarity_score",
        "value": 0.9231
      },
      {
        "user_id": "user_001",
        "exam_id": "exam_spring_2024_01",
        "timestamp": "2024-05-08T10:30:00Z",
        "metric": "flagged_pair_count",
        "value": 2
      }
    ]
  },
  "message": "Risk data fetched successfully"
}
```

---

### `GET /api/module16/report?exam_id=`
Returns the full stored similarity report for a given exam, with integrity verification.

**Auth:** JWT required | **Role:** `teacher` only

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "exam_id": "exam_spring_2024_01",
    "analyzed_at": "2024-05-08T10:30:00Z",
    "analyzed_by": "teacher_001",
    "threshold_used": 0.75,
    "total_responses": 45,
    "total_flagged": 3,
    "integrity_verified": true,
    "flagged_pairs": [...],
    "per_student_max": { "user_001": 0.9231, "user_007": 0.9231 }
  },
  "message": "Similarity report fetched"
}
```

**`integrity_verified: false`** means the stored report was modified after it was written — a security alert.

---

## 3. MongoDB

**Collection used:** `similarity_results` (write)  
**Collection read:** `responses`, `exams`

**Document schema (`similarity_results`):**
```json
{
  "exam_id":          "string",
  "analyzed_at":      "ISO8601",
  "analyzed_by":      "user_id of teacher",
  "threshold_used":   0.75,
  "total_responses":  45,
  "total_flagged":    3,
  "flagged_pairs":    [ { "question_id", "student_a", "student_b", "score" } ],
  "per_student_max":  { "user_id": highest_score },
  "integrity_hash":   "SHA-256 hex string"
}
```

---

## 4. Integration with Module 17

Module 17 (Risk Scoring) calls:
```
GET /api/module16/risk-data?user_id={id}&exam_id={id}
```

The `max_similarity_score` metric maps to the `Similarity Score` component in the risk formula:
```
Risk Score = (0.3 × Tab Switches) + (0.2 × Idle Time) + (0.3 × Similarity Score) + (0.2 × Fast Answering)
```

Module 16's score is already normalized between 0.0 and 1.0, so Module 17 can use it directly.

---

## 5. Running the Module

```bash
cd module_16
pip install -r requirements.txt
python app.py
```

Server starts on `http://localhost:5016`

---

## 6. Integration Tests

Per spec section 27.8:

```bash
# 1. JWT test — expired token should return 401
curl -X POST http://localhost:5016/api/module16/check-similarity \
  -H "Authorization: Bearer EXPIRED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"exam_id": "test"}'
# Expected: 401

# 2. Health test — must respond within 1 second
curl http://localhost:5016/api/module16/health
# Expected: 200, status: healthy

# 3. State test — analysis on non-existent exam should return 404
curl -X POST http://localhost:5016/api/module16/check-similarity \
  -H "Authorization: Bearer VALID_TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"exam_id": "nonexistent_exam"}'
# Expected: 404

# 4. Injection test — MongoDB operator in exam_id should be rejected
curl -X POST http://localhost:5016/api/module16/check-similarity \
  -H "Authorization: Bearer VALID_TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"exam_id": {"$gt": ""}}'
# Expected: 400
```