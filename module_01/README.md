
# Module 01: Secure Authentication

## Security Concept
**bcrypt password hashing + OTP MFA**

## Endpoints to Implement
```
POST /api/module01/register
POST /api/module01/login
POST /api/module01/verify-otp
GET  /api/module01/exam-state/{exam_id}
```

## What Security Problem Does This Solve?
_[Fill in by your group]_

## What Attack Does This Prevent?
_[Fill in by your group]_

## How Is It Implemented?
_[Fill in by your group]_

## Setup
```bash
pip install -r requirements.txt
python app.py
```

## Testing
```bash
# Health check
curl http://localhost:5001/api/module01/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5001/api/module01/your-endpoint
```
