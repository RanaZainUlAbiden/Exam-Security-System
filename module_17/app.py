# module_17/app.py
# MODULE 17: RISK SCORING & DASHBOARD
# Aggregates all module data and computes risk score
# PORT: 5017

import sys, os, datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests as req
from flask import Flask, request, render_template_string
from shared.jwt_helper import jwt_required, role_required
from shared.db_config import get_db
from shared.logging_helper import send_log
from shared.response_helper import success_response, error_response

import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
MODULE_NAME = "Module_17_RiskScoring"
PORT = 5017
MODULE_BASE_URL = os.getenv("MODULE_BASE_URL", "").rstrip("/")


def module_url(port, path):
    if MODULE_BASE_URL:
        return f"{MODULE_BASE_URL}{path}"
    return f"http://127.0.0.1:{port}{path}"

# Module URLs for risk data
RISK_MODULES = {
    "tab_monitor":     module_url(5010, "/api/module10/risk-data"),
    "clipboard":       module_url(5011, "/api/module11/risk-data"),
    "activity":        module_url(5012, "/api/module12/risk-data"),
    "multi_session":   module_url(5014, "/api/module14/risk-data"),
    "behavioral":      module_url(5015, "/api/module15/risk-data"),
    "similarity":      module_url(5016, "/api/module16/risk-data"),
    "secure_timer":    module_url(5008, "/api/module08/risk-data"),
}

def normalize(value, max_val):
    """Normalize a value to 0.0 - 1.0 range."""
    if max_val == 0:
        return 0.0
    return min(1.0, value / max_val)

def fetch_metric(url, user_id, exam_id, token):
    """Fetch risk data from a module."""
    try:
        r = req.get(url, params={"user_id": user_id, "exam_id": exam_id},
                    headers={"Authorization": f"Bearer {token}"}, timeout=3)
        if r.status_code == 200:
            return r.json().get("data", {}).get("data", [])
    except:
        pass
    return []

def compute_risk_score(metrics: dict) -> dict:
    """
    Risk Score Formula (from project document):
    Risk = (0.3 × Tab Switches) +
           (0.2 × Idle Time) +
           (0.3 × Similarity Score) +
           (0.2 × Fast Answering)
    """
    tab_switches     = metrics.get("tab_switch_count", 0)
    idle_time_sec    = metrics.get("idle_time_seconds", 0)
    similarity_score = metrics.get("max_similarity_score", 0.0)
    fast_answering   = metrics.get("fast_answering", 0)
    paste_count      = metrics.get("paste_count", 0)
    multi_session    = metrics.get("active_session_count", 0)

    # Normalize each metric
    tab_score        = normalize(tab_switches, 10)
    idle_score       = normalize(idle_time_sec, 600)
    similarity_norm  = float(similarity_score)
    fast_score       = float(fast_answering)

    # Base formula from doc
    base_score = (0.3 * tab_score) + (0.2 * idle_score) + \
                 (0.3 * similarity_norm) + (0.2 * fast_score)

    # Bonus risk from paste events
    paste_bonus = normalize(paste_count, 5) * 0.1

    # Multi-session is automatic high risk
    if multi_session > 1:
        base_score = min(1.0, base_score + 0.3)

    final_score = min(1.0, base_score + paste_bonus)
    percentage  = round(final_score * 100, 2)

    if percentage >= 70:
        level = "HIGH"
    elif percentage >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "score":      percentage,
        "level":      level,
        "breakdown": {
            "tab_switches":     tab_switches,
            "idle_time_sec":    idle_time_sec,
            "similarity_score": similarity_score,
            "fast_answering":   fast_answering,
            "paste_count":      paste_count,
            "multi_session":    multi_session > 1
        }
    }


def calculate_and_store_risk(db, user_id, exam_id, token):
    metrics = {}
    for name, url in RISK_MODULES.items():
        data_list = fetch_metric(url, user_id, exam_id, token)
        for item in data_list:
            metrics[item.get("metric", name)] = item.get("value", 0)

    result = compute_risk_score(metrics)
    score_doc = {
        "user_id": user_id,
        "exam_id": exam_id,
        "score": result["score"],
        "level": result["level"],
        "breakdown": result["breakdown"],
        "metrics": metrics,
        "computed_at": datetime.datetime.utcnow().isoformat() + "Z"
    }

    db["risk_scores"].update_one(
        {"user_id": user_id, "exam_id": exam_id},
        {"$set": score_doc},
        upsert=True
    )

    if result["level"] == "HIGH":
        send_log(MODULE_NAME, "SECURITY", user_id, exam_id,
                 "high_risk_student", {"score": result["score"], "level": result["level"]})

    return score_doc

@app.route("/api/module17/health", methods=["GET"])
def health():
    return {"module": MODULE_NAME, "status": "healthy", "dependencies": ["mongodb"], "version": "1.0.0"}, 200

@app.route("/api/module17/risk-score/<user_id>/<exam_id>", methods=["GET"])
@jwt_required
def risk_score(user_id, exam_id):
    """Compute and return risk score for a student in an exam."""
    token   = request.headers.get("Authorization","").split(" ")[-1]
    db      = get_db()
    score_doc = calculate_and_store_risk(db, user_id, exam_id, token)

    return success_response(
        data={
            "user_id": user_id,
            "exam_id": exam_id,
            "score": score_doc["score"],
            "level": score_doc["level"],
            "breakdown": score_doc["breakdown"]
        },
        message="Risk score computed"
    )

@app.route("/api/module17/dashboard", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def dashboard_api():
    """JSON dashboard — all students risk scores for an exam."""
    exam_id = request.args.get("exam_id")
    if not exam_id:
        return error_response(400, "exam_id required")

    db = get_db()
    token = request.headers.get("Authorization", "").split(" ")[-1]
    participant_ids = set(db["student_timers"].distinct("user_id", {"exam_id": exam_id}))
    participant_ids.update(db["responses"].distinct("user_id", {"exam_id": exam_id}))

    for user_id in participant_ids:
        calculate_and_store_risk(db, user_id, exam_id, token)

    scores = list(db["risk_scores"].find({"exam_id": exam_id}, {"_id": 0}).sort("score", -1))

    high   = [s for s in scores if s.get("level") == "HIGH"]
    medium = [s for s in scores if s.get("level") == "MEDIUM"]
    low    = [s for s in scores if s.get("level") == "LOW"]

    return success_response(
        data={"exam_id": exam_id, "total_students": len(scores),
              "summary": {"high": len(high), "medium": len(medium), "low": len(low)},
              "students": scores},
        message="Dashboard data retrieved"
    )

@app.route("/dashboard", methods=["GET"])
@jwt_required
@role_required(["teacher"])
def dashboard_html():
    """Simple HTML dashboard for teacher."""
    exam_id = request.args.get("exam_id", "")
    db      = get_db()
    scores  = list(db["risk_scores"].find({"exam_id": exam_id} if exam_id else {}, {"_id": 0}).sort("score", -1))

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Risk Dashboard</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f5f5f5; }
            h1   { color: #2c8c6e; }
            table { width: 100%; border-collapse: collapse; background: white; }
            th    { background: #2c8c6e; color: white; padding: 10px; }
            td    { padding: 10px; border-bottom: 1px solid #ddd; text-align: center; }
            .HIGH   { color: red;    font-weight: bold; }
            .MEDIUM { color: orange; font-weight: bold; }
            .LOW    { color: green;  font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🔐 Risk Scoring Dashboard</h1>
        <p>Exam: <b>{{ exam_id }}</b> | Total Students: <b>{{ total }}</b></p>
        <table>
            <tr><th>Student</th><th>Score</th><th>Risk Level</th>
                <th>Tab Switches</th><th>Similarity</th><th>Idle(s)</th></tr>
            {% for s in scores %}
            <tr>
                <td>{{ s.user_id }}</td>
                <td>{{ s.score }}%</td>
                <td class="{{ s.level }}">{{ s.level }}</td>
                <td>{{ s.breakdown.tab_switches }}</td>
                <td>{{ s.breakdown.similarity_score }}</td>
                <td>{{ s.breakdown.idle_time_sec }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    from jinja2 import Template
    return Template(html).render(scores=scores, exam_id=exam_id, total=len(scores))

if __name__ == "__main__":
    print(f"Module 17 — Risk Scoring running on port {PORT}")
    print(f"   GET /api/module17/risk-score/<user_id>/<exam_id>")
    print(f"   GET /api/module17/dashboard?exam_id=X")
    print(f"   GET /dashboard?exam_id=X  (HTML)")
    app.run(port=PORT, debug=True)
