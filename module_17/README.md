# Module 17: Risk Scoring & Dashboard

## Security Concept
**Security analytics and risk score generation**

## Endpoints to Implement
```
GET  /api/module17/risk-score/{user_id}/{exam_id}
GET  /api/module17/dashboard
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
curl http://localhost:5017/api/module17/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5017/api/module17/your-endpoint
```
