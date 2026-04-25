# 📜 INTEGRATION CONTRACT
## Exam Security System — All Groups MUST Read & Follow

> ⚠️ This document is MANDATORY. Modules that don't follow this contract will be rejected during integration.

---

## 1. Shared Credentials

```python
JWT_SECRET    = "exam_security_UET_2024_secret_key"
MONGO_URI     = "mongodb://localhost:27017/exam_security"
DATABASE_NAME = "exam_security"
```

**NEVER change these values. Use exactly as-is.**

---

## 2. JWT Token Structure

Module 1 (Auth) issues tokens. All other modules only VALIDATE.

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": "string",
    "username": "string",
    "role": "student | teacher",
    "session_id": "string",
    "device_fingerprint_hash": "string",
    "exp": 1700000000
  }
}
```

### JWT Validation Rule (Every Endpoint Except Login/Register):
```
1. Extract token from header: Authorization: Bearer <token>
2. Verify using JWT_SECRET with HS256
3. Check expiration
4. Return HTTP 401 if invalid
```

---

## 3. Standard HTTP Error Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 | Success | Request processed |
| 400 | Bad Request | Missing/invalid parameters |
| 401 | Unauthorized | Invalid or missing JWT |
| 403 | Forbidden | Valid JWT, insufficient role |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Wrong exam state |
| 500 | Internal Error | Module crashed |
| 503 | Service Unavailable | Dependency down |

### Error Response Format (EXACT):
```json
{
  "status": "error",
  "error_code": 401,
  "message": "JWT expired",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Success Response Format (EXACT):
```json
{
  "status": "success",
  "data": {},
  "message": "Operation completed"
}
```

---

## 4. Logging Gateway (MANDATORY)

**NEVER write directly to MongoDB logs collection.**
All logs MUST go through this endpoint:

```
POST http://localhost:5000/api/logs/write
```

Request Body:
```json
{
  "module": "Module_10_TabMonitor",
  "level": "INFO",
  "user_id": "abc123",
  "exam_id": "exam456",
  "action": "tab_switch_detected",
  "details": {"count": 3},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Log Levels: `INFO` | `WARNING` | `ERROR` | `SECURITY`

---

## 5. Health Check (MANDATORY)

Every module MUST implement:
```
GET /api/moduleXX/health
```

Response:
```json
{
  "module": "Module_1_Auth",
  "status": "healthy",
  "dependencies": ["mongodb"],
  "version": "1.0.0"
}
```

---

## 6. Exam State Machine

All exam-related modules MUST respect this flow:

```
NOT_STARTED → DEVICE_VERIFIED → TEACHER_APPROVED → ACTIVATION_VALID → IN_PROGRESS → SUBMITTED → ANALYZING → COMPLETED
```

| State | Who Handles |
|-------|------------|
| NOT_STARTED → DEVICE_VERIFIED | Module 3 |
| DEVICE_VERIFIED → TEACHER_APPROVED | Teacher action |
| TEACHER_APPROVED → ACTIVATION_VALID | Module 4 |
| ACTIVATION_VALID → IN_PROGRESS | Module 1 |
| IN_PROGRESS → SUBMITTED | Module 8 |
| SUBMITTED → ANALYZING | Module 17 |
| ANALYZING → COMPLETED | Module 17 |

**Rules:**
- Timer (Module 8) only runs during `IN_PROGRESS`
- Monitoring (Modules 10-13) only active during `IN_PROGRESS`
- Answer submission only during `IN_PROGRESS`
- Risk scoring runs during `ANALYZING`

Get exam state: `GET /api/exam/state/{exam_id}` — provided by Module 1

---

## 7. Database Collections Access

| Collection | Can Read | Can Write |
|-----------|---------|----------|
| users | Module 1, 5 | Module 1 only |
| devices | Module 1, 3, 14 | Module 3 only |
| exams | Module 1,4,5,6,7,8 | Module 1, 4 |
| questions | Module 6, 7, 16 | Module 6 only |
| responses | Module 8, 12, 16 | Module 8 only |
| logs | ALL (via API only) | Logging Gateway only |
| risk_scores | Module 17 | Module 17 only |

---

## 8. Risk Data Endpoint (Modules 10,11,12,14,15,16 MUST implement)

Module 17 will call this on each module:
```
GET /api/moduleXX/risk-data?user_id={id}&exam_id={id}
```

Response:
```json
{
  "module": "Module_10_TabMonitor",
  "data": [
    {
      "user_id": "string",
      "exam_id": "string",
      "timestamp": "2024-01-15T10:30:00Z",
      "metric": "tab_switch_count",
      "value": 3
    }
  ]
}
```

---

## 9. API URL Convention

```
POST /api/module{XX}/{action}
GET  /api/module{XX}/{action}
```

Examples:
```
POST /api/module01/login
GET  /api/module01/health
POST /api/module10/tab-switch
GET  /api/module17/risk-score
```

---

## 10. Integration Testing Checklist

Before final submission, your module MUST pass ALL:

- [ ] JWT test: Call your API with expired token → get HTTP 401
- [ ] Logging test: Generate a log → verify it appears in shared logs
- [ ] Health test: GET /health returns 200 within 1 second
- [ ] State test: Wrong exam state → returns HTTP 409
- [ ] No direct MongoDB log writes (use logging gateway only)
