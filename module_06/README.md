# Module 06: Secure Question Delivery

## Security Concept
**Confidential encrypted question API**

## Endpoints to Implement
```
GET  /api/module06/questions/{exam_id}
POST /api/module06/release-questions
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
curl http://localhost:5006/api/module06/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5006/api/module06/your-endpoint
```
