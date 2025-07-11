# logging_middleware.py
import requests
import json
import os

# Important: In a real app, load this from environment variables or a secure config
# For this exam, you can put your actual token here if not using env vars
AFFORDMED_ACCESS_TOKEN = os.getenv("AFFORDMED_API_TOKEN", "YOUR_ACTUAL_ACCESS_TOKEN_FROM_GET_TOKEN_PY_OUTPUT")

LOG_API_URL = "http://20.244.56.144/evaluation-service/logs"

def log_event(stack: str, level: str, package: str, message: str):
    """
    Logs an event to the Afford Medicals evaluation service.
    This function now uses the globally configured AFFORDMED_ACCESS_TOKEN.
    """
    if not AFFORDMED_ACCESS_TOKEN or AFFORDMED_ACCESS_TOKEN == "YOUR_ACTUAL_ACCESS_TOKEN_FROM_GET_TOKEN_PY_OUTPUT":
        print("Error: AFFORDMED_ACCESS_TOKEN not configured. Cannot send logs.")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AFFORDMED_ACCESS_TOKEN}"
    }

    payload = {
        "stack": stack.lower(),
        "level": level.lower(),
        "package": package.lower(),
        "message": message
    }

    # --- Basic validation for log constraints (as per previous instructions) ---
    valid_stacks = ["backend", "frontend"]
    valid_levels = ["debug", "info", "warn", "error", "fatal"]
    valid_backend_packages = ["cache", "controller", "cron_job", "db", "domain", "handler", "repository", "route", "service"]
    valid_frontend_packages = ["api", "component", "hook", "page", "state", "style"]
    valid_common_packages = ["auth", "config", "middleware", "utils"]

    if stack.lower() not in valid_stacks:
        print(f"Logging Warning: Invalid stack '{stack}'.")
        return
    if level.lower() not in valid_levels:
        print(f"Logging Warning: Invalid level '{level}'.")
        return

    current_package = package.lower()
    if stack.lower() == "backend" and current_package not in (valid_backend_packages + valid_common_packages):
        print(f"Logging Warning: Invalid package '{package}' for backend stack.")
        return
    elif stack.lower() == "frontend" and current_package not in (valid_frontend_packages + valid_common_packages):
        print(f"Logging Warning: Invalid package '{package}' for frontend stack.")
        return
    # --- End validation ---

    try:
        response = requests.post(LOG_API_URL, headers=headers, json=payload, timeout=5) # Add timeout
        response.raise_for_status()
        # print(f"Log event sent successfully: {response.json()}") # Uncomment for debug
        # It's generally good not to print success logs to console in production
    except requests.exceptions.RequestException as e:
        print(f"Error sending log event to AffordMed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"AffordMed Log API Response: {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred during logging: {e}")

# Example of how to set the token for local testing (remove for production/env var setup)
# If you don't want to use environment variables:
# AFFORDMED_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ..." # PASTE YOUR REAL TOKEN HERE