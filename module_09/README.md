# Module 09: Input Validation

## 🔐 Security Concept
NoSQL Injection and XSS Prevention through secure input validation and sanitization for MongoDB environments.



## 🚀 Module Overview
This module validates and sanitizes all user inputs before they are processed by the system. It acts as a security layer to prevent malicious payloads from compromising the exam system, with specific focus on MongoDB injection attacks.


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
- Inject MongoDB operators to manipulate queries
- Store XSS payloads in the database
- Bypass validation using Unicode encoding tricks
- Exploit BSON type confusion
- Break application logic with malformed inputs
  
This module ensures all inputs are verified before processing.


## ⚠️ What Attack Does This Prevent?

### 1. MongoDB/NoSQL Injection
Examples:
- `{"$ne": null}` - Operator injection in JSON
- `$where: 1==1` - JavaScript injection
- `$regex: .*` - ReDoS via regex injection
- `admin.password` - Dot notation injection
- `ObjectId("...")` - BSON type injection

### 2. Cross-Site Scripting (XSS)
Examples:
- `<script>alert(1)</script>` - Script Injection
- `<img src=x onerror=alert(1)>` - Event Handler Injection
- `javascript:alert(1)` - Protocol Handler Injection
- `<iframe src="evil.com">` - Iframe Injection
- `<svg onload=alert(1)>` - SVG Injection

### 3. Unicode Bypass Attacks
Examples:
- Full-width characters used to bypass pattern matching
- Null byte injection
- Control character injection


## ⚙️ How It Is Implemented?

This module uses a multi-layer defense approach:

### ✔ Unicode Normalization
Converts all Unicode characters to NFKC form to prevent encoding-based bypass attacks. Removes null bytes and control characters.


### ✔ Pattern Detection (MongoDB + XSS)
Separate pattern sets for:
- MongoDB Injection: Operators (`$ne`, `$gt`, `$where`), methods (`.find()`, `.aggregate()`), BSON types
- XSS Vectors: Script tags, event handlers, protocol handlers, dangerous functions

### ✔ Field Validation
Strict validation rules per field type:
- `username`: 3-20 chars, alphanumeric + underscore
- `email`: RFC 5321 compliant format
- `password`: 6-50 characters
- `text`: 1-500 chars with safe punctuation
- `answer`: 1-1000 chars, exam-specific format
- `object_id`: MongoDB ObjectId format (24 hex chars)

### ✔ Multi-Step Sanitization
1. Unicode Normalization (NFKC)
2. HTML Tag Removal (including nested script tags)
3. HTML Entity Decoding (prevents entity-based bypass)
4. MongoDB Operator Removal (strips $where, $regex, etc.)
5. Dangerous Character Stripping (null bytes, control chars)
6. Whitespace Normalization
7. Trimming


### ✔ JWT Authentication
All endpoints require a valid JWT token via `Authorization: Bearer <token>` header to ensure only authenticated users can access the validation and sanitization services.

### ✔ Secure Logging
All attacks (blocked and detected) and validations are logged via centralized logging gateway with:
- Attack type and pattern matched
- Client IP address
- User ID and exam ID
- Input length statistics


## 📦 Supported Field Types
| Field Type | Pattern                | Max Length | MongoDB Safe |
| ---------- | ---------------------- | ---------- | ------------ |
| username   | `^[a-zA-Z0-9_]{3,20}$` | 20         | Yes          |
| password   | `^.{6,50}$`            | 50         | Yes          |
| email      | RFC 5321 compliant     | 254        | Yes          |
| text       | Safe punctuation       | 500        | No*          |
| answer     | Extended chars         | 1000       | No*          |
| object_id  | `^[a-fA-F0-9]{24}$`    | 24         | Yes          |

*Fields marked "No" require additional MongoDB-specific sanitization

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
  "value": "test_123",
  "exam_id": "exam_001"
}'
```
## 3. MongoDB Injection Attempt
```bash
curl --location 'http://localhost:5009/api/module09/validate-input' \
--header 'Authorization: Bearer <your_token>' \
--header 'Content-Type: application/json' \
--data '{
  "field": "username",
  "value": "{\"$ne\": null}",
  "exam_id": "exam_001"
}'
```
## 4. XSS Attack
```bash
curl --location 'http://localhost:5009/api/module09/validate-input' \
--header 'Authorization: Bearer <your_token>' \
--header 'Content-Type: application/json' \
--data '{
  "field": "text",
  "value": "<script>alert(1)</script>",
  "exam_id": "exam_001"
}'
```
## 5. Invalid Format
```bash
curl --location 'http://localhost:5009/api/module09/validate-input' \
--header 'Authorization: Bearer <your_token>' \
--header 'Content-Type: application/json' \
--data '{
  "field": "username",
  "value": "!!!@@@",
  "exam_id": "exam_001"
}'
```
## 6.Sanitize Endpoint
```bash
curl --location 'http://localhost:5009/api/module09/sanitize' \
--header 'Authorization: Bearer <your_token>' \
--header 'Content-Type: application/json' \
--data '{
  "value": "<script>Hello</script>",
  "exam_id": "exam_001"
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
## 8. Dot Notation Injection
```bash
curl --location 'http://localhost:5009/api/module09/validate-input' \
--header 'Authorization: Bearer <your_token>' \
--header 'Content-Type: application/json' \
--data '{
  "field": "username",
  "value": "admin.password",
  "exam_id": "exam_001"
}'
```

## 📊 Expected Results

| Test Case              | Endpoint       | Expected Result               |
| ---------------------- | -------------- | ----------------------------- |
| Valid Input            | validate-input | 200 Success + sanitized value |
| MongoDB Injection      | validate-input | 400 Blocked (Malicious input) |
| XSS Attack             | validate-input | 400 Blocked (Malicious input) |
| Invalid Format         | validate-input | 400 Validation error          |
| Dot Notation Injection | validate-input | 400 Blocked (Malicious input) |
| Sanitize with XSS      | sanitize       | 200 Success + cleaned value   |
| Missing JWT            | validate-input | 401 Unauthorized              |
| Input Too Long         | validate-input | 400 Exceeds maximum length    |

## 🔒 Security Features

- **MongoDB Injection Detection** (operators, methods, BSON types)
- **XSS Prevention** (tags, event handlers, protocols)
- **Unicode Normalization** (prevents encoding bypass)
- **Field-Based Validation Rules**
- **Multi-Step Sanitization Pipeline**
- **Dot Notation Injection Protection**
- **BSON Type Injection Detection**
- **JWT Authentication Required**
- **Centralized Security Logging**
- **Input Length Limiting**

## 👨‍💻 Integration Notes
- **Works with Module 01** (Authentication) for JWT validation
- **Protects Module 06** (Question Delivery) from injection
- **Protects Module 07** (Question Randomization) input
- **Sends logs to Logging Gateway** for centralized monitoring
- **Compatible with Module 17** (Risk Scoring) for attack pattern analysis
- **No direct database manipulation** - validation/sanitization only
- **MongoDB-specific protection** tailored for the exam system database

## 📌 Summary
Module 09 ensures that no malicious or malformed input enters the system by combining Unicode normalization, pattern-based attack detection, field-specific validation, and multi-step sanitization in a layered security approach. With specific focus on MongoDB NoSQL injection prevention, this module is critical for maintaining the integrity and security of the online examination system's database and preventing stored XSS attacks.

