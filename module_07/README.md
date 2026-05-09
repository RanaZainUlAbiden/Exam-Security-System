# Module 07: Question Randomization

## Security Concept
**Anti-collusion question shuffling**

## Endpoints to Implement
```
GET  /api/module07/randomized-questions/{exam_id}
```

## What Security Problem Does This Solve?
"In a traditional online exam, all students see questions in the same order, making answer 
sharing through whispering, screen peeking, or WhatsApp groups highly effective. Module 7 
assigns every student a unique, cryptographically seeded shuffle of both questions and 
answer options, so any answer one student shares becomes completely useless to others 
since they are looking at entirely different questions. This makes real-time collusion, 
screen peeking, and answer key leaks ineffective without disrupting the student's own 
experience, as the same student always receives the same order on every page refresh."

## What Attack Does This Prevent?
"It prevents Exam Collusion and Answer Sharing, where students share answers during 
an exam through whispering, screen peeking, or online messaging apps like WhatsApp, making 
cheating completely ineffective."

## How Is It Implemented?
"It is implemented by generating a unique cryptographic seed for each student using 
their user_id and exam_id, which shuffles both the question order and MCQ options 
independently, so every student receives a completely different arrangement of questions 
and answers making any shared answer useless to others."

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