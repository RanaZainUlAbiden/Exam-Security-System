# shared/db_config.py
# =============================================
# DO NOT MODIFY THIS FILE
# Shared MongoDB connection for all modules
# =============================================

from pymongo import MongoClient

import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI     = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "exam_security")

_client = None

def get_db():
    """
    Returns the shared MongoDB database instance.
    Call this in your module to get DB access.

    Usage:
        from shared.db_config import get_db
        db = get_db()
        users = db["users"].find({"role": "student"})
    """
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client[DATABASE_NAME]


# Collection name constants — use these, don't hardcode strings
COLLECTIONS = {
    "users":       "users",
    "devices":     "devices",
    "exams":       "exams",
    "questions":   "questions",
    "responses":   "responses",
    "logs":        "logs",        # Access via logging gateway ONLY
    "risk_scores": "risk_scores",
}
