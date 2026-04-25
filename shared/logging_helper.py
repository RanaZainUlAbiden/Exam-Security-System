# shared/logging_helper.py
# =============================================
# DO NOT MODIFY THIS FILE
# All modules use this to send logs
# NEVER write directly to MongoDB logs collection
# =============================================

import requests
import datetime

LOGGING_GATEWAY_URL = "http://localhost:5000/api/logs/write"

LOG_LEVELS = ["INFO", "WARNING", "ERROR", "SECURITY"]


def send_log(module_name: str, level: str, user_id: str,
             exam_id: str, action: str, details: dict = {}):
    """
    Send a log entry to the central logging gateway.

    Args:
        module_name: e.g. "Module_10_TabMonitor"
        level:       "INFO" | "WARNING" | "ERROR" | "SECURITY"
        user_id:     user's ID string
        exam_id:     exam's ID string
        action:      short action description e.g. "tab_switch_detected"
        details:     any extra data as a dict

    Usage:
        from shared.logging_helper import send_log
        send_log("Module_10_TabMonitor", "SECURITY", user_id, exam_id,
                 "tab_switch_detected", {"count": 3})
    """
    if level not in LOG_LEVELS:
        level = "INFO"

    payload = {
        "module":    module_name,
        "level":     level,
        "user_id":   str(user_id),
        "exam_id":   str(exam_id),
        "action":    action,
        "details":   details,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

    try:
        response = requests.post(LOGGING_GATEWAY_URL, json=payload, timeout=3)
        return response.status_code == 202
    except requests.exceptions.ConnectionError:
        # Logging gateway down — don't crash the module
        print(f"[WARNING] Logging gateway unavailable. Log dropped: {action}")
        return False
    except Exception as e:
        print(f"[WARNING] Failed to send log: {e}")
        return False
