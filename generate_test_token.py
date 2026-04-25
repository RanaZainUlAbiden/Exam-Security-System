"""
generate_test_token.py
======================
Run this script to get a test JWT token for development.
All groups can use this to test their module endpoints
WITHOUT waiting for Module 01 to be complete.

Usage:
    python generate_test_token.py

    python generate_test_token.py --role teacher
    python generate_test_token.py --role student
"""

import jwt
import datetime
import argparse
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

JWT_SECRET    = "exam_security_UET_2024_secret_key"
JWT_ALGORITHM = "HS256"

parser = argparse.ArgumentParser(description="Generate test JWT token")
parser.add_argument("--role",     default="student", choices=["student", "teacher"])
parser.add_argument("--user_id",  default="test_user_001")
parser.add_argument("--username", default="test_student")
args = parser.parse_args()

payload = {
    "user_id":                 args.user_id,
    "username":                args.username,
    "role":                    args.role,
    "session_id":              "test_session_abc123",
    "device_fingerprint_hash": "test_device_hash_xyz",
    "exp":                     datetime.datetime.utcnow() + datetime.timedelta(hours=24)
}

token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

print("\n" + "="*60)
print(f"  TEST JWT TOKEN ({args.role.upper()})")
print("="*60)
print(f"\nToken:\n{token}")
print(f"\nUser ID:  {args.user_id}")
print(f"Username: {args.username}")
print(f"Role:     {args.role}")
print(f"Expires:  24 hours from now")
print("\nUsage in curl:")
print(f'  curl -H "Authorization: Bearer {token}" http://localhost:500X/api/moduleXX/your-endpoint')
print("="*60 + "\n")
