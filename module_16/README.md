# Module 16: Answer Similarity Detection

## Security Concept
**TF-IDF + Cosine similarity to detect copying**

## Endpoints to Implement
```
POST /api/module16/check-similarity
GET  /api/module16/risk-data
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
curl http://localhost:5016/api/module16/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5016/api/module16/your-endpoint
```
