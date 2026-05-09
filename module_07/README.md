# Module 07: Question Randomization

## Security Concept
**Anti-collusion question shuffling**

## Endpoints to Implement
```
GET  /api/module07/randomized-questions/{exam_id}
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
curl http://localhost:5007/api/module07/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5007/api/module07/your-endpoint
```