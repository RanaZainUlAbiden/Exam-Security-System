# Module 04: Activation Code Security

## Security Concept
**One-time tokens with time-based validation**

## Endpoints to Implement
```
POST /api/module04/generate-code
POST /api/module04/validate-code
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
curl http://localhost:5004/api/module04/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5004/api/module04/your-endpoint
```
