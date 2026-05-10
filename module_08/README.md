# Module 08: Secure Timer

## Security Concept
Timer runs **entirely on the server**. Client only receives remaining time — it cannot modify, pause, or rewind it. All submissions are validated against server-side timestamps.

## What Security Problem Is Solved?
Students manipulating browser-side timers using dev tools, extensions, or system clock changes to get extra time.

## What Attack Is Prevented?
- **Time Manipulation** — browser/JS timer tampered → server time unchanged
- **Late Submission** — post-expiry submission rejected at server level
- **System Clock Hack** — server uses `datetime.utcnow()`, not client time
- **Fast Answering Abuse** — detected and flagged for Module 17

## How Is It Implemented?
1. Teacher creates exam with `duration_minutes`
2. Student calls `/start-timer` → server records `start_time = utcnow()`
3. Student calls `/time-remaining` → server computes `end_time - utcnow()`
4. Student submits → server checks if `utcnow() < end_time`
5. Time expired → auto-submit triggered, late submission rejected

---

## Endpoints

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/api/module08/create-exam` | Teacher | Create exam with duration |
| POST | `/api/module08/start-timer` | Student | Start exam timer |
| GET | `/api/module08/time-remaining/<exam_id>` | Student | Get remaining time |
| POST | `/api/module08/submit-exam` | Student | Submit answers |
| GET | `/api/module08/exam-status/<exam_id>` | Teacher | Monitor all students |
| GET | `/api/module08/risk-data` | Module 17 | Fast answering metric |
| GET | `/api/module08/health` | Anyone | Health check |

---

## ⚠️ Important for Module 16 (Answer Similarity)
Answers are saved to `responses` collection in this EXACT format:
```json
{
  "user_id": "string",
  "exam_id": "string",
  "question_id": "string",
  "answer_text": "string"
}
```

---

## Postman Testing Guide

### Step 1: Get Tokens
```bash
python generate_test_token.py --role teacher
python generate_test_token.py --role student --user_id "student_001"
```

### Step 2: Teacher Creates Exam
```
POST http://localhost:5008/api/module08/create-exam
Headers: Authorization: Bearer [TEACHER_TOKEN]

Body:
{
  "exam_id": "exam001",
  "exam_title": "Mid Term CS101",
  "duration_minutes": 1,
  "total_questions": 3
}
```
Expected: `"state": "NOT_STARTED"` ✅

### Step 3: Student Starts Timer
```
POST http://localhost:5008/api/module08/start-timer
Headers: Authorization: Bearer [STUDENT_TOKEN]

Body: {"exam_id": "exam001"}
```
Expected: `remaining_seconds: 60, state: IN_PROGRESS` ✅

### Step 4: Check Remaining Time
```
GET http://localhost:5008/api/module08/time-remaining/exam001
Headers: Authorization: Bearer [STUDENT_TOKEN]
```
Expected: Countdown decreasing ✅

### Step 5: Submit Answers
```
POST http://localhost:5008/api/module08/submit-exam
Headers: Authorization: Bearer [STUDENT_TOKEN]

Body:
{
  "exam_id": "exam001",
  "answers": [
    {"question_id": "q1", "answer_text": "Paris is the capital of France"},
    {"question_id": "q2", "answer_text": "Newton discovered gravity"}
  ]
}
```
Expected: `"submitted": true` ✅

### Step 6: Security Test — Late Submission
Wait for 1 minute (timer expires) → try to submit again
Expected: `409 — Time expired. Late submission rejected.` ✅

### Step 7: Teacher View Status
```
GET http://localhost:5008/api/module08/exam-status/exam001
Headers: Authorization: Bearer [TEACHER_TOKEN]
```
Expected: All student timers + status ✅

---

## Database Collections
- `exams` — exam info + state
- `student_timers` — per-student start/end times
- `responses` — submitted answers (read by Module 16)
