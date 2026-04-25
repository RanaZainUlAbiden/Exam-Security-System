"""
integration_test.py
====================
Run this script to check health of all modules.
Usage: python integration_test.py
"""

import requests

MODULES = {
    "Logging Gateway":          "http://localhost:5000/api/logs/health",
    "Module 01 - Auth":         "http://localhost:5001/api/module01/health",
    "Module 02 - Session":      "http://localhost:5002/api/module02/health",
    "Module 03 - Device":       "http://localhost:5003/api/module03/health",
    "Module 04 - Activation":   "http://localhost:5004/api/module04/health",
    "Module 05 - RBAC":         "http://localhost:5005/api/module05/health",
    "Module 06 - Questions":    "http://localhost:5006/api/module06/health",
    "Module 07 - Randomize":    "http://localhost:5007/api/module07/health",
    "Module 08 - Timer":        "http://localhost:5008/api/module08/health",
    "Module 09 - Validation":   "http://localhost:5009/api/module09/health",
    "Module 10 - Tab Monitor":  "http://localhost:5010/api/module10/health",
    "Module 11 - Clipboard":    "http://localhost:5011/api/module11/health",
    "Module 12 - Activity Log": "http://localhost:5012/api/module12/health",
    "Module 13 - Secure Log":   "http://localhost:5013/api/module13/health",
    "Module 14 - Multi Session":"http://localhost:5014/api/module14/health",
    "Module 15 - Behavioral":   "http://localhost:5015/api/module15/health",
    "Module 16 - Similarity":   "http://localhost:5016/api/module16/health",
    "Module 17 - Risk Score":   "http://localhost:5017/api/module17/health",
}

print("\n" + "="*55)
print("   INTEGRATION HEALTH CHECK — ALL MODULES")
print("="*55)

passed = 0
failed = 0

for name, url in MODULES.items():
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            print(f"  ✅  {name}")
            passed += 1
        else:
            print(f"  ❌  {name} — HTTP {r.status_code}")
            failed += 1
    except requests.exceptions.ConnectionError:
        print(f"  🔴  {name} — NOT RUNNING")
        failed += 1
    except Exception as e:
        print(f"  ❌  {name} — ERROR: {e}")
        failed += 1

print("="*55)
print(f"  Passed: {passed}/{len(MODULES)}   Failed: {failed}/{len(MODULES)}")
print("="*55 + "\n")
