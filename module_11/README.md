# Module 11: Clipboard Monitoring

## Security Concept
**Detect copy-paste data leakage**

## Endpoints to Implement
```
POST /api/module11/clipboard-event
GET  /api/module11/risk-data
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
curl http://localhost:5011/api/module11/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5011/api/module11/your-endpoint
```
