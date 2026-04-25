# Module 02: Secure Session Management

## Security Concept
**JWT session management + expiry enforcement**

## Endpoints to Implement
```
POST /api/module02/validate-session
POST /api/module02/invalidate-session
GET  /api/module02/session-status
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
curl http://localhost:5002/api/module02/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5002/api/module02/your-endpoint
```
