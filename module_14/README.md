# Module 14: Multi-Session Detection

## Security Concept
**Prevent multiple concurrent logins**

## Endpoints to Implement
```
POST /api/module14/check-session
GET  /api/module14/risk-data
```

## What Security Problem Does This Solve?
In online exams, students can share their login credentials with friends.
One student shares their username and password, and multiple people log in
from different devices at the same time. This completely breaks academic
integrity because:

Someone else can attempt the exam on behalf of the original student
Multiple people can collaborate and share answers in real time
The system has no way to know who is actually taking the exam

## What Attack Does This Prevent?
This module prevents the Simultaneous Login Attack (also called
Credential Sharing Attack):

Student A shares their username + password with Student B
Student A logs in from their phone and starts the exam
Student B tries to log in from a different device using the same credentials
Module 14 detects this — sees that Student A already has an active session
Student B's login is immediately blocked with HTTP 409
The incident is logged as a SECURITY event
Module 17 is notified and the student's risk score increases

## How Is It Implemented?
Session Tracking
When a student successfully logs in (via Module 1), a session document
is saved in the devices collection in MongoDB with:

user_id — who is logged in
device_id — which device they are using
status: "active" — marks this as a live session
login_at — when the session started
last_activity — updated every 5 minutes via heartbeat

Detection Logic
Before allowing any new login, the module queries MongoDB:
Is there already a document where user_id = X AND status = "active"?

YES → Block the new login with HTTP 409 Conflict
NO  → Allow login, save new session document

Session Cleanup
Sessions are marked as closed when:

Student logs out (Module 1 calls /close-session)
Exam is submitted (Module 8 calls /close-session)
App crashes or internet disconnects → session automatically terminates after 15 minutes of no heartbeat/activity
System timeout thread detects inactive sessions and closes them automatically

## Setup
```bash
pip install -r requirements.txt
python app.py
```

## Testing
```bash
# Health check
curl http://localhost:5014/api/module14/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5014/api/module14/your-endpoint
```
