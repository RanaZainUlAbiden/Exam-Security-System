# Module 10: Tab Monitoring

## Security Concept
**Detect app/tab switching during exam**

## Endpoints to Implement
```
POST /api/module10/tab-switch
GET  /api/module10/risk-data
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
curl http://localhost:5010/api/module10/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5010/api/module10/your-endpoint
```
