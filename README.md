# 🔐 Secure Online Examination System
### IS Lab Semester Project — UET Lahore

---

## 📌 Project Overview
A multi-layered secure online examination system built as a class-wide integration project.
- **60 Students | 17 Groups | 17 Security Modules**
- **Integration Lead:** Rana Zain Ul Abiden

---

## 🛠️ Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React.js |
| Backend | Python (Flask) |
| Database | MongoDB (localhost:27017) |
| Auth | JWT (HS256) |
| Password Hashing | bcrypt |
| Log Integrity | SHA-256 |
| AI/ML | Scikit-learn, TF-IDF, Cosine Similarity |

---

## 📁 Repository Structure
```
exam-security-system/
├── shared/                  ← Common utilities (JWT, DB, Logging) — READ ONLY for groups
├── logging_gateway/         ← Central logging service — DO NOT MODIFY
├── frontend/                ← React.js frontend
├── module_01/               ← Secure Authentication
├── module_02/               ← Secure Session Management
├── module_03/               ← Device Fingerprinting
├── module_04/               ← Activation Code Security
├── module_05/               ← RBAC
├── module_06/               ← Secure Question Delivery
├── module_07/               ← Question Randomization
├── module_08/               ← Secure Timer
├── module_09/               ← Input Validation
├── module_10/               ← Tab Monitoring
├── module_11/               ← Clipboard Monitoring
├── module_12/               ← Activity Logging
├── module_13/               ← Secure Logging (SHA-256)
├── module_14/               ← Multi-Session Detection
├── module_15/               ← Behavioral Analysis
├── module_16/               ← Answer Similarity Detection
├── module_17/               ← Risk Scoring & Dashboard
└── docker-compose.yml       ← Run all modules together
```

---

## ⚙️ Module Port Assignments
| Module | Name | Port |
|--------|------|------|
| Logging Gateway | Central Logs | 5000 |
| Module 1 | Secure Authentication | 5001 |
| Module 2 | Session Management | 5002 |
| Module 3 | Device Fingerprinting | 5003 |
| Module 4 | Activation Code | 5004 |
| Module 5 | RBAC | 5005 |
| Module 6 | Question Delivery | 5006 |
| Module 7 | Randomization | 5007 |
| Module 8 | Secure Timer | 5008 |
| Module 9 | Input Validation | 5009 |
| Module 10 | Tab Monitor | 5010 |
| Module 11 | Clipboard Monitor | 5011 |
| Module 12 | Activity Logging | 5012 |
| Module 13 | Secure Logging | 5013 |
| Module 14 | Multi-Session | 5014 |
| Module 15 | Behavioral Analysis | 5015 |
| Module 16 | Answer Similarity | 5016 |
| Module 17 | Risk Scoring | 5017 |

---

## 🚀 Getting Started (Each Group)

### 1. Clone the repo
```bash
git clone https://github.com/Infromation-Security-Final-Project/Exam-Security-System.git
cd Exam-Security-System
```

### 2. Go to your module folder
```bash
cd module_XX   # replace XX with your module number
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Copy shared config
```bash
# Already included in boilerplate — don't change JWT_SECRET or MONGO_URI
```

### 5. Run your module
```bash
python app.py
```

---

## 📏 GOLDEN RULES (Every Group MUST Follow)

1. ✅ **Only work inside your own `module_XX` folder**
2. ✅ **Never write directly to MongoDB logs collection** — use logging gateway API
3. ✅ **Always validate JWT** on every endpoint (except login/register)
4. ✅ **Implement `/api/moduleXX/health` endpoint**
5. ✅ **Use exact error codes** defined in INTEGRATION_CONTRACT.md
6. ✅ **Provide Postman collection** with all your API endpoints
7. ❌ **Never change shared/ or logging_gateway/ folders**
8. ❌ **Never change someone else's module folder**

---

## 📞 Contact
**Integration Lead:** Rana Zain Ul Abiden
- All integration questions → WhatsApp Group
- Code issues → GitHub Issues tab (tag your module number)

---

## Demo Deployment

The full React frontend, logging gateway, and all 17 Flask modules can run as
one Docker web service backed by MongoDB Atlas. See [DEPLOYMENT.md](DEPLOYMENT.md)
for the verified Render deployment steps.
