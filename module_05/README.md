# Module 05: Role-Based Access Control

## Security Concept
**Role-based authorization for students/teachers**

## Endpoints to Implement
```
GET  /api/module05/check-permission
GET  /api/module05/user-role
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
curl http://localhost:5005/api/module05/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5005/api/module05/your-endpoint
```
