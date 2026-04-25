# Module 14: Multi-Session Detection

## Security Concept
**Prevent multiple concurrent logins**

## Endpoints to Implement
```
POST /api/module14/check-session
GET  /api/module14/risk-data
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
curl http://localhost:5014/api/module14/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5014/api/module14/your-endpoint
```
