# Module 15: Behavioral Analysis

## Security Concept
**Rule-based anomaly detection**

## Endpoints to Implement
```
POST /api/module15/analyze
GET  /api/module15/risk-data
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
curl http://localhost:5015/api/module15/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5015/api/module15/your-endpoint
```
