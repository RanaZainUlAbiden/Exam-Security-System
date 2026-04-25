# Module 12: Activity Logging

## Security Concept
**Complete exam audit trail**

## Endpoints to Implement
```
POST /api/module12/log-activity
GET  /api/module12/risk-data
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
curl http://localhost:5012/api/module12/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5012/api/module12/your-endpoint
```
