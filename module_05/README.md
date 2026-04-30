# Module 05: Role-Based Access Control (RBAC)

## Security Concept
**Role-Based Authorization**

## What security problem is solved?
In an online examination system, knowing *who* a user is (Authentication) is not enough. We must restrict *what* they can do (Authorization). This module centrally manages and enforces permissions, preventing standard users from accessing administrative or instructor-level functionalities.

## What attack is prevented?
- **Vertical Privilege Escalation:** Prevents a `student` from executing API endpoints meant for a `teacher` (e.g., grading exams or approving students).
- **Stale Token Exploitation:** By cross-referencing the role inside the JWT with the actual `users` database collection, it prevents a user whose role was demoted from exploiting a still-valid session token.

## How is it implemented?
1. **JWT Extraction:** Uses the centralized `@jwt_required` decorator to securely identify the user.
2. **Database Verification:** Queries the `users` collection (read-access permitted) to verify the user's current role.
3. **Whitelist Matrix:** Checks the requested `action` against a strict dictionary of allowed actions (`PERMISSIONS`).
4. **Audit Logging:** Any unauthorized attempt is immediately blocked with an **HTTP 403 Forbidden** error and logged to the Central Gateway with a `SECURITY` flag to trigger threat detection.

## Why and How should other modules use it. 
**If your module performs a sensitive action (e.g., deleting a question, starting a timer, or viewing a log), you must call Module 05 for authorization.**

### 1. The Call Pattern (Python)
In your module's route, use the `requests` library to ask Module 05 for permission:

```python
import requests

@app.route("/api/moduleXX/your-action")
@jwt_required
def your_action():
    token = request.headers.get("Authorization")
    
    # Ask Module 05 if this user can do 'your_specific_action'
    rbac_url = "http://localhost:5005/api/module05/check-permission?action=your_specific_action"
    rbac_resp = requests.get(rbac_url, headers={"Authorization": token})
    
    if rbac_resp.status_code != 200:
        return error_response(403, "RBAC: You do not have permission for this action")

    # Proceed with your logic...

## Setup
```bash
pip install -r requirements.txt
python app.py
```

## Testing
```bash
# Health check
curl http://localhost:5005/api/module05/health

# Test with JWT (get token from Module 1 first)
curl -H "Authorization: Bearer <your_token>" http://localhost:5005/api/module05/check-permission
```