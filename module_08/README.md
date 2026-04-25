# Module 08: Secure Timer

## Security Concept
**Server-side timing to prevent manipulation**

## Endpoints to Implement
```
POST /api/module08/start-timer
GET  /api/module08/time-remaining/{exam_id}
POST /api/module08/submit-exam
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
curl http://localhost:5008/api/module08/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5008/api/module08/your-endpoint
```
