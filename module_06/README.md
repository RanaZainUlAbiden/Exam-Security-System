# Module 06: Secure Question Delivery

Module 06 provides secure storage and controlled delivery of exam questions.
It enforces role-based controls for teachers, verifies JWT for protected routes,
and restricts student access to released questions during the correct exam state.

## Security Objective

Ensure question confidentiality and controlled release so students cannot access
exam content before the exam is officially in progress.

## Security Problems Solved

- Prevents unauthorized users from adding or releasing questions.
- Prevents students from fetching questions before exam start.
- Prevents leakage of teacher identity fields in question responses.
- Provides auditable logs for question creation, release, access, and denied attempts.

## Threats Mitigated

- Early question access / question paper leakage.
- Privilege escalation (student trying teacher-only actions).
- Token-less or invalid-token API access.
- Silent abuse attempts without traceability.

## Implementation Summary

- JWT protection on all functional routes using shared decorators.
- Teacher-only enforcement on creation and release routes.
- Student access gate based on exam state check (`IN_PROGRESS`).
- Question release flag (`released`) to separate draft vs visible questions.
- Centralized logging through logging gateway (`INFO` and `SECURITY` events).

## Module Details

- Module Name: `Module_06_QuestionDelivery`
- Default Port in Code: `6006`
- Database Collections Used:
	- `questions` (read/write)
	- `exams` (read for state validation)

## API Endpoints

### 1) Health Check

- Method: `GET`
- Path: `/api/module06/health`
- Auth: Not required

Success response:

```json
{
	"module": "Module_06_QuestionDelivery",
	"status": "healthy",
	"dependencies": ["mongodb"],
	"version": "1.0.0"
}
```

### 2) Add Questions (Teacher only)

- Method: `POST`
- Path: `/api/module06/add-questions`
- Auth: JWT required
- Role: `teacher`

Request body:

```json
{
	"exam_id": "exam_001",
	"questions": [
		{
			"question_text": "What is CIA triad?",
			"question_type": "text",
			"options": [],
			"marks": 2
		}
	]
}
```

Success response:

```json
{
	"status": "success",
	"data": {
		"exam_id": "exam_001",
		"questions_added": 1
	},
	"message": "1 questions added"
}
```

### 3) Release Questions (Teacher only)

- Method: `POST`
- Path: `/api/module06/release-questions`
- Auth: JWT required
- Role: `teacher`

Request body:

```json
{
	"exam_id": "exam_001"
}
```

Success response:

```json
{
	"status": "success",
	"data": {
		"released": 10
	},
	"message": "Questions released"
}
```

### 4) Get Released Questions

- Method: `GET`
- Path: `/api/module06/questions/<exam_id>`
- Auth: JWT required
- Roles:
	- `student`: allowed only if exam state is `IN_PROGRESS`
	- `teacher`: can access released questions

Success response:

```json
{
	"status": "success",
	"data": {
		"exam_id": "exam_001",
		"questions": [
			{
				"question_id": "a1b2c3d4e5f6",
				"exam_id": "exam_001",
				"question_text": "What is CIA triad?",
				"question_type": "text",
				"options": [],
				"marks": 2,
				"created_at": "2026-05-09T10:00:00Z",
				"released": true
			}
		],
		"total": 1
	},
	"message": "Questions delivered"
}
```

Error cases:

- `400` for missing required payload fields.
- `401` for missing/invalid/expired JWT.
- `403` for role violations or student access outside `IN_PROGRESS`.

## Setup and Run

From `module_06` directory:

```bash
pip install -r requirements.txt
python app.py
```

Service starts on:

```text
http://localhost:6006
```

## Quick Testing

### Health

```bash
curl http://localhost:6006/api/module06/health
```

### Add questions (teacher token)

```bash
curl -X POST http://localhost:6006/api/module06/add-questions \
	-H "Authorization: Bearer <TEACHER_JWT>" \
	-H "Content-Type: application/json" \
	-d '{"exam_id":"exam_001","questions":[{"question_text":"Q1","marks":1}]}'
```

### Release questions (teacher token)

```bash
curl -X POST http://localhost:6006/api/module06/release-questions \
	-H "Authorization: Bearer <TEACHER_JWT>" \
	-H "Content-Type: application/json" \
	-d '{"exam_id":"exam_001"}'
```

### Fetch questions (student token)

```bash
curl http://localhost:6006/api/module06/questions/exam_001 \
	-H "Authorization: Bearer <STUDENT_JWT>"
```

## Logging Behavior

This module sends logs to the central logging gateway for:

- questions added
- questions released
- questions accessed
- denied question access attempts

## Notes

- Use shared JWT and response helpers exactly as provided.
- Do not write logs directly to MongoDB; always use logging gateway.
- Ensure `exams` collection has valid `state` values for student access control.
