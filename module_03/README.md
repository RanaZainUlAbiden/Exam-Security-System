# Module 03: Device Fingerprinting

## Security Concept
Each student account is **bound to one device**. A SHA-256 fingerprint is computed from device properties (user agent, platform, screen resolution, timezone). Any login attempt from a different device is detected, flagged, and blocked.

## What Security Problem Is Solved?
Students sharing account credentials with others. One student logging in from multiple machines during an exam.

## What Attack Is Prevented?
- **Account Sharing** — credentials leaked to another student won't work on their device
- **Impersonation** — someone else using your account gets blocked
- **Multi-device cheating** — student cannot use two devices simultaneously

## How Is It Implemented?
1. Student logs in first time → device components sent → SHA-256 fingerprint computed → stored in `devices` collection
2. Every exam session start → `verify-device` called → fingerprint compared
3. Mismatch → `403 Forbidden` + alert saved + security log sent
4. Teacher can view alerts, resolve them, or reset a device (e.g. student changed laptop)

---

## Fingerprint Components
| Component | Example |
|-----------|---------|
| user_agent | `Mozilla/5.0 (Windows NT 10.0; Win64; x64)` |
| platform | `Win32` |
| screen_resolution | `1920x1080` |
| timezone | `Asia/Karachi` |
| language | `en-US` |
| color_depth | `24` |

All components → JSON string → SHA-256 → 64-char hex fingerprint

---

## Endpoints

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/api/module03/register-device` | Student | Register device on first login |
| POST | `/api/module03/verify-device` | Student | Verify device before exam |
| GET | `/api/module03/student-device/<user_id>` | Teacher | View student's device |
| GET | `/api/module03/alerts` | Teacher | View all mismatch alerts |
| POST | `/api/module03/resolve-alert` | Teacher | Mark alert as resolved |
| POST | `/api/module03/reset-device` | Teacher | Clear device (student changed laptop) |
| GET | `/api/module03/risk-data` | Module 17 | Risk metrics |
| GET | `/api/module03/health` | Anyone | Health check |

---

## Setup
```bash
pip install -r requirements.txt
python app.py
```

---

## Postman Testing Guide

### Step 1: Get Test Tokens
```bash
python generate_test_token.py --role student --user_id "student_001"
python generate_test_token.py --role teacher
```

---

### Step 2: Health Check
```
GET http://localhost:5003/api/module03/health
```
Expected: `{"status": "healthy"}`

---

### Step 3: Register Device (Student)
```
POST http://localhost:5003/api/module03/register-device

Headers:
  Authorization: Bearer [STUDENT_TOKEN]
  Content-Type: application/json

Body:
{
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  "platform": "Win32",
  "screen_resolution": "1920x1080",
  "timezone": "Asia/Karachi",
  "language": "en-US",
  "color_depth": "24"
}
```
Expected: `"status": "registered"` ✅

---

### Step 4: Same Device — Verify Again
Same request dobara karo
Expected: `"status": "known_device"` ✅

---

### Step 5: Verify Device Before Exam
```
POST http://localhost:5003/api/module03/verify-device

Headers:
  Authorization: Bearer [STUDENT_TOKEN]
  Content-Type: application/json

Body: (same as register)
{
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  "platform": "Win32",
  "screen_resolution": "1920x1080",
  "timezone": "Asia/Karachi"
}
```
Expected: `"verified": true` ✅

---

### Step 6: Security Test — Different Device
```
POST http://localhost:5003/api/module03/register-device

Body: (different device — changed screen_resolution)
{
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  "platform": "Win32",
  "screen_resolution": "1366x768",
  "timezone": "Asia/Karachi"
}
```
Expected: `403 Forbidden — Device mismatch detected` ✅

---

### Step 7: Teacher — View Alerts
```
GET http://localhost:5003/api/module03/alerts

Headers:
  Authorization: Bearer [TEACHER_TOKEN]
```
Expected: Alert list for student_001 ✅

---

### Step 8: Teacher — Reset Device
```
POST http://localhost:5003/api/module03/reset-device

Headers:
  Authorization: Bearer [TEACHER_TOKEN]
  Content-Type: application/json

Body:
{
  "user_id": "student_001",
  "reason": "Student changed laptop"
}
```
Expected: Device cleared ✅

---

## Database Collections Used
- `devices` — registered device per student
- `device_alerts` — suspicious login attempts
