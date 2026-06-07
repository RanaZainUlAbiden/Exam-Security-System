
# Module 01: Secure Authentication

## Security Concept
**Email-based login + bcrypt password hashing + OTP MFA**

## Endpoints to Implement
```
POST /api/module01/register
POST /api/module01/login
POST /api/module01/verify-otp
GET  /api/module01/exam-state/{exam_id}
```

## What Security Problem Does This Solve?
It ensures that users authenticate with a registered email address, a hashed
password, and a short-lived one-time password before receiving a JWT.

## What Attack Does This Prevent?
It reduces password database exposure risk with bcrypt, blocks direct JWT access
without OTP verification, and prevents public users from self-registering as
teachers after the first teacher account exists.

## How Is It Implemented?
Students register with `email`, `password`, and role `student`. Passwords are
stored as bcrypt hashes. Registration generates a six-digit OTP and sends it to
the registered email when SMTP is configured. OTP verification marks the account
verified and issues the JWT. Later login also accepts email and password,
generates a fresh OTP, and requires OTP verification before issuing a JWT. The
OTP expires after five minutes and is never returned by the API response.

For classroom demos, `DEMO_OTP` can be set in the environment. If SMTP is not
configured, Module 01 falls back to the demo OTP or prints a development OTP to
server logs.

## Setup
```bash
pip install -r requirements.txt
python app.py
```

## Testing
```bash
# Health check
curl http://localhost:5001/api/module01/health

# Register a student and request verification OTP
curl -X POST http://localhost:5001/api/module01/register \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"TestPass123","role":"student"}'

# Login and request OTP
curl -X POST http://localhost:5001/api/module01/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"TestPass123"}'

# Verify OTP and receive JWT
curl -X POST http://localhost:5001/api/module01/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<USER_ID>","otp":"<OTP>"}'
```
