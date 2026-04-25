# Module 03: Device Fingerprinting

## Security Concept
**Device binding to prevent account sharing**

## Endpoints to Implement
```
POST /api/module03/register-device
GET  /api/module03/verify-device
POST /api/module03/risk-data
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
curl http://localhost:5003/api/module03/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5003/api/module03/your-endpoint
```
