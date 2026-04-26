# Module 09: Input Validation

## 🔐 Security Concept
SQL Injection, NoSQL Injection, and XSS Prevention through secure input validation and sanitization.


## 🚀 Module Overview
This module is responsible for validating and sanitizing all user inputs before they are processed by the system. It acts as a security layer to prevent malicious payloads from compromising the exam system.


## 🌐 Endpoints Implemented

### 1. Validate Input (Security Check)
```
POST /api/module09/validate-input
```
### 2. Sanitize Input (Cleaning Only)
```
POST /api/module09/sanitize
```


## ❗ What Security Problem Does This Solve?

Online examination systems are vulnerable to malicious user inputs that can:
- Manipulate database queries
- Inject malicious scripts
- Break application logic
- Steal or corrupt data

This module ensures all inputs are verified before processing.


## ⚠️ What Attack Does This Prevent?

### 1. SQL Injection
Examples:
- `' OR 1=1 --`
- `"; DROP TABLE users; --`

### 2. NoSQL Injection
Examples:
- `$ne: null`
- `$gt`, `$lt`, `$or`, `$where`

### 3. Cross-Site Scripting (XSS)
Examples:
- `<script>alert(1)</script>`
- `<img src=x onerror=alert(1)>`

### 4. Command / Injection Patterns
- `&&`, `||`
- backticks
- script-based payloads


## ⚙️ How It Is Implemented?

This module uses a multi-layer defense approach:

### ✔ Pattern Detection
Regex-based detection of known attack signatures.

### ✔ Field Validation
Strict validation rules per field (username, email, text, etc.).

### ✔ Secure Sanitization
- Removes HTML tags using BeautifulSoup
- Removes dangerous characters like `$ { } < > / ;`
- Normalizes whitespace

### ✔ JWT Authentication
All endpoints require valid JWT token.

### ✔ Secure Logging
All attacks and actions are logged via centralized logging gateway.


## 📦 Setup

```bash
pip install -r requirements.txt
python app.py
```
## 🧪 Testing
## 1. Health check
```bash
curl http://localhost:5009/api/module09/health
```
## 2. Validate Input (JWT Required)
```bash
curl --location 'http://localhost:5009/api/module09/validate-input' \
--header 'Authorization: Bearer <your_token>' \
--header 'Content-Type: application/json' \
--data '{
  "field": "username",
  "value": "test_123"
}'
```
## 3. MongoDB Injection Attempt
```bash
curl --location 'http://localhost:5009/api/module09/validate-input' \
--header 'Authorization: Bearer <your_token>' \
--header 'Content-Type: application/json' \
--data '{
  "field": "username",
  "value": "$ne: null"
}
```
## 4. XSS Attack
```bash
curl --location 'http://localhost:5009/api/module09/sanitize' \
--header 'Authorization: Bearer <your_token>' \
--header 'Content-Type: application/json' \
--data '{
  "field": "text",
  "value": "<script>alert(1)</script>"
}'
```
## 5. Invalid Format
```bash
curl --location 'http://localhost:5009/api/module09/validate-input' \
--header 'Authorization: Bearer <your_token>' \
--header 'Content-Type: application/json' \
--data '{
  "field": "username",
  "value": "!!!@@@"
}'
```
## 6.Sanitize Endpoint
```bash
curl --location 'http://localhost:5009/api/module09/sanitize' \
--header 'Authorization: Bearer <your_token>' \
--header 'Content-Type: application/json' \
--data '{
  "value": "<script>Hello</script>"
}'
```
## 7. Missing JWT
```bash
curl --location 'http://localhost:5009/api/module09/validate-input' \
--header 'Content-Type: application/json' \
--data '{
  "field": "username",
  "value": "test_123"
}'
```

## 📊 Expected Results

| Test Case         | Result                     |
| ----------------- | -------------------------- |
| Valid Input       | Success + sanitized output |
| MongoDB Injection | Blocked (400 error)        |
| XSS Input         | Blocked (400 error)        |
| Invalid Format    | Validation error           |
| Missing JWT       | 401 Unauthorized           |

## 🔒 Security Features

- **Input Validation (field-based rules)**
- **Injection Detection (SQL/NoSQL/XSS)**
- **Secure Sanitization Engine**
- **JWT Authentication**
- **Centralized Logging Support**
  
## 👨‍💻 Integration Notes
- **Works with Module 01 (Authentication)**
- **Sends logs to Logging Gateway**
- **Compatible with Risk Scoring Module (17)**
- **No direct database manipulation**

## 📌 Summary
Module 09 ensures that no malicious or malformed input enters the system by combining validation, sanitization, and attack detection in a layered security approach. This is critical for maintaining the integrity and security of the online examination system.