# 🚀 GROUP ONBOARDING GUIDE
## Exam Security System — IS Lab Project

---

## Step 1: GitHub Setup

1. GitHub account banao: https://github.com
2. Apna username integration lead ko WhatsApp karo
3. Repo invite aaye toh accept karo
4. Repo clone karo:

```bash
git clone https://github.com/RanaZainUlAbiden/Exam-Security-System.git
cd Exam-Security-System
```

---

## Step 2: Apna Module Folder Dhundho

```
module_01/  → Group 01
module_02/  → Group 02
...
module_17/  → Group 17
```

**Sirf apne folder mein kaam karna hai. Kisi aur ke folder ko touch nahi karna.**

---

## Step 3: Dependencies Install Karo

```bash
cd module_XX       # apna number daalo
pip install -r requirements.txt
```

---

## Step 4: Test Token Lao (Module 01 ke bina bhi test kar sakte ho)

```bash
# Repo root mein jao
cd ..
pip install PyJWT
python generate_test_token.py --role student
```

Ye ek JWT token dega — apni endpoints test karne ke liye use karo.

---

## Step 5: Apna Module Chalao

```bash
cd module_XX
python app.py
```

---

## Step 6: Health Check Karo

```bash
curl http://localhost:50XX/api/moduleXX/health
```

Ye aana chahiye:
```json
{"module": "Module_XX_Name", "status": "healthy"}
```

---

## MANDATORY Cheezein (Har Group Ke Liye)

- [ ] `/api/moduleXX/health` endpoint working
- [ ] Har endpoint pe JWT validation
- [ ] Logs logging gateway ke through bhejna (`shared/logging_helper.py`)
- [ ] Standard error codes use karna (401, 403, 400, etc.)
- [ ] Postman collection banana apni APIs ki
- [ ] `module_XX/README.md` fill karna (security concept explain karna)

---

## Important Files — Zaroor Parho

| File | Kya Hai |
|------|---------|
| `INTEGRATION_CONTRACT.md` | Sab rules — MANDATORY |
| `shared/jwt_helper.py` | JWT validate karne ka code |
| `shared/logging_helper.py` | Log bhejne ka code |
| `shared/response_helper.py` | Standard API responses |
| `generate_test_token.py` | Test JWT banana |

---

## Help Chahiye?

- **Integration issues** → WhatsApp pe Rana bhai ko message karo
- **Code issues** → GitHub Issues tab pe issue create karo, module number tag karo

---

## GOLDEN RULES

1. ✅ Sirf apne `module_XX/` folder mein kaam karo
2. ✅ `shared/` folder ko kabhi modify mat karo
3. ✅ Logs direct MongoDB mein mat likhna — `send_log()` use karo
4. ✅ JWT validate karo har endpoint pe
5. ❌ Dusre ki files mat chhona
