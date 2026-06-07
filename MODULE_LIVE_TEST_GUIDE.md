# Live Module Testing Guide

Live application: `https://secure-exam-system-9gzh.onrender.com`

The Render deployment contains the React web application, logging gateway, and
all 17 Flask modules. Changes merged or pushed to the GitHub `main` branch are
automatically rebuilt and deployed by Render. Sharing the live link gives
classmates access to the deployed application, but it does not give them GitHub
write access. Repository collaborators should push a branch and open a pull
request so their code can be reviewed before it reaches `main`.

## Shared Test Setup

Use Postman for API-only checks. Create these environment variables:

- `BASE_URL`: `https://secure-exam-system-9gzh.onrender.com`
- `TEACHER_TOKEN`: JWT returned by the teacher OTP flow
- `STUDENT_TOKEN`: JWT returned by the student OTP flow
- `STUDENT2_TOKEN`: JWT returned for a second student
- `STUDENT_ID` and `STUDENT2_ID`: IDs returned by registration/login
- `EXAM_ID`: a unique value such as `group_test_2026_01`

Teacher demo login:

- Username: `demo_teacher`
- Password: `DemoExam#2026`
- Demo OTP: `692386`

Students should create their own unique student accounts from the Register tab.
Teacher self-registration is intentionally disabled after the first teacher is
provisioned, because allowing a visitor to choose the teacher role is a
privilege-escalation vulnerability.

For protected API calls, send:

```text
Authorization: Bearer {{TEACHER_TOKEN}}
Content-Type: application/json
```

## Module 01: Secure Authentication

1. Open the live app and register a student with a unique username.
2. Log in with the username and password. Confirm the API response does not
   contain an `otp` field.
3. Enter OTP `692386`. Confirm the student dashboard opens.
4. Try a wrong password and wrong OTP. Both must return HTTP 401.
5. Repeat the same registration. It must return HTTP 409.

API: `POST /api/module01/register`, `/login`, and `/verify-otp`.

## Module 02: Secure Session Management

1. Log in and save the JWT as `STUDENT_TOKEN`.
2. Call `POST /api/module02/validate-session`; expect `valid: true`.
3. Call `GET /api/module02/session-status`; expect a positive
   `remaining_seconds`.
4. Call `POST /api/module02/invalidate-session`.
5. Reuse the same JWT on `/api/module05/user-role`; expect HTTP 401.

The normal UI Logout button now calls Module 02 before clearing browser storage.

## Module 03: Device Fingerprinting

1. Register and log in as a new student. The web app automatically registers
   the browser fingerprint.
2. Log in again from the same browser; expect `known_device`.
3. Log in from a browser/device with different screen and platform data; expect
   HTTP 403 and a device mismatch alert.
4. As teacher, call `GET /api/module03/alerts` to see unresolved alerts.
5. Test reset with `POST /api/module03/reset-device` and the student's
   `user_id`.

## Module 04: Activation Code Security

1. As teacher, create an exam and open Activation Codes.
2. Generate one code per student. Confirm every code is eight characters.
3. As student, enter the exam ID and code; expect successful validation.
4. Submit the same code again through Postman; expect HTTP 409.
5. Submit `WRONGCOD`; expect HTTP 401.

API: `POST /api/module04/generate-code` and `/validate-code`.

## Module 05: Role-Based Access Control

1. With a teacher token, call:
   `GET /api/module05/check-permission?permission=create_exam`.
   Expect HTTP 200 and `allowed: true`.
2. Repeat with a student token. Expect HTTP 403.
3. Call `GET /api/module05/user-role` with each token and confirm the role.
4. Call `GET /api/module05/all-permissions` as student; expect HTTP 403.

## Module 06: Secure Question Delivery

1. As teacher, create an exam in the web app.
2. Add three questions and click Save and Release All.
3. Before the student starts their own timer, call
   `GET /api/module06/questions/{{EXAM_ID}}`; expect HTTP 403.
4. Validate an activation code and start the exam.
5. Repeat the request; expect exactly the released questions and no teacher
   metadata.

## Module 07: Question Randomization

1. Prepare two student accounts and two activation codes for the same exam.
2. Start the exam for both students.
3. Call `GET /api/module07/randomized-questions/{{EXAM_ID}}` with each token.
4. Confirm each student receives all questions but in a different order.
5. Repeat for the same student and confirm that student's order stays stable.

## Module 08: Secure Server-Side Timer

1. As teacher, create a 30-minute exam.
2. Try to start it as a student before activation; expect HTTP 409.
3. Validate a code and open the exam. Confirm the timer starts near `30:00`.
4. Refresh the page or change the computer clock. The server time must continue
   without resetting.
5. Submit once; expect success. Submit again; expect HTTP 409.
6. As teacher, open Monitor and Risk and confirm submitted/active totals.

## Module 09: Input Validation

Use the student token:

1. POST `{"exam_id":{"$gt":""},"answer":"normal"}` to
   `/api/module09/validate-input`; expect HTTP 400 and `nosql_injection`.
2. POST `{"answer":"<script>alert('xss')</script>"}`; expect HTTP 400 and
   `xss`.
3. POST `{"answer":"A clean security answer"}`; expect HTTP 200 and
   `safe: true`.

The exam page now validates every entered answer through Module 09 before
submission.

## Module 10: Tab Monitoring

1. Start an exam as a student.
2. Switch to another browser tab and return at least five times.
3. Call
   `GET /api/module10/risk-data?user_id={{STUDENT_ID}}&exam_id={{EXAM_ID}}`
   with the teacher token.
4. Confirm `tab_switch_count` is at least five.
5. Send a tab event before starting an exam; expect HTTP 409.

## Module 11: Clipboard Monitoring

1. During an active exam, attempt copy, paste, and cut in the answer area.
2. Confirm the UI blocks the operation.
3. Call
   `GET /api/module11/risk-data?user_id={{STUDENT_ID}}&exam_id={{EXAM_ID}}`
   with the teacher token.
4. Confirm paste/copy counts were recorded without storing clipboard content.
5. Send an event outside an active exam; expect HTTP 409.

## Module 12: Activity Logging

1. During an active exam, right-click in the page. The context menu must be
   blocked.
2. As teacher, call
   `GET /api/module12/get-logs/{{EXAM_ID}}?user_id={{STUDENT_ID}}`.
3. Confirm a `right_click_attempt` entry exists.
4. POST an unknown action such as `invented_action`; expect HTTP 400.
5. POST an activity outside an active exam; expect HTTP 409.

## Module 13: Secure Logging and SHA-256 Integrity

1. Complete several exam actions so shared logs exist.
2. As teacher, call
   `GET /api/module13/integrity-report/{{EXAM_ID}}`.
3. Expect `total_logs > 0`, `tampered_count: 0`, and
   `integrity_percentage: 100`.
4. Verify a known log ID with
   `GET /api/module13/verify-log/{LOG_ID}`; expect `is_intact: true`.
5. A direct unauthenticated write to `/api/logs/write` must return HTTP 401.

## Module 14: Multi-Session Detection

1. Log in as the same student in browser A and browser B.
2. Each login automatically registers its Module 14 session.
3. Browser B should terminate the older active session.
4. In browser A, make another protected request; expect HTTP 401.
5. Call `GET /api/module14/check-session` in browser B and confirm only one
   active session remains.

A second distinct login is required. Repeating registration with the same JWT
is idempotent and is not treated as a second session.

## Module 15: Behavioral Analysis

This module currently has API verification rather than a dedicated screen.
During an active exam:

1. POST `{"exam_id":"{{EXAM_ID}}","event_type":"idle","value":301}` to
   `/api/module15/log-behavior` with the student token.
2. POST a `typing_speed` event with value `180`.
3. As teacher, POST
   `{"user_id":"{{STUDENT_ID}}","exam_id":"{{EXAM_ID}}"}` to
   `/api/module15/analyze`.
4. Confirm `flagged: true` and the anomaly rules are listed.
5. A student token calling `/analyze` must receive HTTP 403.

## Module 16: Answer Similarity Detection

1. Have two students submit identical answers for the same questions.
2. After both submit, open the teacher Monitor and Risk tab. The UI runs
   similarity analysis before calculating risk.
3. Or POST `{"exam_id":"{{EXAM_ID}}"}` to
   `/api/module16/check-similarity` with the teacher token.
4. Confirm `flagged_pairs > 0` and no raw answer text is returned.
5. Call `/api/module16/report?exam_id={{EXAM_ID}}`; expect
   `integrity_verified: true`.

## Module 17: Risk Scoring and Dashboard

1. Generate tab, clipboard, activity, behavioral, and similarity evidence.
2. Submit all students' exams.
3. As teacher, open Monitor and Risk and load the exam ID.
4. Confirm both students appear with LOW, MEDIUM, or HIGH scores and a metric
   breakdown.
5. Call the dashboard with a student token; expect HTTP 403.
6. Attempt risk scoring before all students submit; expect HTTP 409 because
   scoring is only allowed in the analysis stage.

## What Each Group Should Report

Each group lead should provide:

1. Screenshot of `/api/moduleXX/health` returning HTTP 200.
2. One successful request and its response.
3. One blocked attack or unauthorized request and its HTTP error.
4. Evidence that a log was created through the shared logging gateway.
5. A short explanation of the threat, defense, and implementation.

The live app is a React web application. The original proposal names an Android
Java/Kotlin APK as mandatory, so the current frontend is suitable for the web
demo but is not an Android deliverable unless the instructor approves the
technology change.
