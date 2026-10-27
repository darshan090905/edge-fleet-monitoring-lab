import os
import json
import base64
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load secrets from .env if present
load_dotenv()

app = Flask(__name__)

# Jira Configuration
JIRA_URL = os.getenv("JIRA_URL", "https://your-domain.atlassian.net").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "your-email@example.com")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "your-jira-api-token")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "OPS")
PORT = int(os.getenv("TICKET_SERVICE_PORT", "5001"))

# In-Memory Deduplication Store: maps alert_key -> ticket_info
# Prevents creating duplicate Jira tickets when Alertmanager fires repeat notifications
open_tickets = {}
ticket_counter = 100

def is_jira_configured():
    return (
        JIRA_API_TOKEN != "your-jira-api-token"
        and JIRA_EMAIL != "your-email@example.com"
        and "atlassian.net" in JIRA_URL
    )

def create_jira_ticket(alertname, instance, severity, summary, description):
    """Creates a real Jira issue via Atlassian REST API, or simulates creation if credentials aren't set."""
    global ticket_counter

    if is_jira_configured():
        auth_str = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "fields": {
                "project": {"key": JIRA_PROJECT_KEY},
                "summary": f"[{severity.upper()}] {alertname} on {instance}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": f"{summary}\n\nDetails: {description}\nDevice: {instance}\nSeverity: {severity}"}
                            ]
                        }
                    ]
                },
                "issuetype": {"name": "Task"}
            }
        }

        try:
            resp = requests.post(f"{JIRA_URL}/rest/api/3/issue", json=payload, headers=headers, timeout=10)
            if resp.status_code in [200, 201]:
                data = resp.json()
                key = data.get("key", "UNKNOWN")
                print(f"[JIRA CLOUD SUCCESS] Created live ticket {key} for {alertname} on {instance}", flush=True)
                return key
            else:
                print(f"[JIRA ERROR {resp.status_code}] Failed to create ticket: {resp.text}", flush=True)
                ticket_counter += 1
                return f"OPS-FALLBACK-{ticket_counter}"
        except Exception as e:
            print(f"[JIRA CONNECTION ERROR] {e}", flush=True)
            ticket_counter += 1
            return f"OPS-FALLBACK-{ticket_counter}"
    else:
        # Local / Mock Mode for immediate verification without Jira account
        ticket_counter += 1
        simulated_key = f"OPS-{ticket_counter}"
        print(f"[TICKET CREATED - SIMULATED MODE] Key: {simulated_key} | Alert: {alertname} | Target: {instance} | Severity: {severity}", flush=True)
        return simulated_key

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "ticket-service",
        "jira_configured": is_jira_configured(),
        "open_tickets_count": len(open_tickets)
    }), 200

@app.route("/tickets", methods=["GET"])
def get_tickets():
    return jsonify({
        "open_tickets": open_tickets,
        "count": len(open_tickets)
    }), 200

@app.route("/alert", methods=["POST"])
def receive_alert():
    data = request.get_json(force=True)
    if not data or "alerts" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    processed = []

    for alert in data.get("alerts", []):
        status = alert.get("status", "firing")
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})

        alertname = labels.get("alertname", "UnknownAlert")
        instance = labels.get("instance", "unknown-device")
        severity = labels.get("severity", "warning")
        summary = annotations.get("summary", "No summary provided")
        description = annotations.get("description", "No description provided")

        dedup_key = f"{alertname}:{instance}"

        if status == "firing":
            # Duplicate prevention check
            if dedup_key in open_tickets:
                existing_ticket = open_tickets[dedup_key]
                print(f"[DUPLICATE BLOCKED] Alert '{dedup_key}' already has an active ticket: {existing_ticket['ticket_id']}. Skipping duplicate.", flush=True)
                processed.append({
                    "dedup_key": dedup_key,
                    "action": "duplicate_suppressed",
                    "ticket_id": existing_ticket["ticket_id"]
                })
            else:
                ticket_id = create_jira_ticket(alertname, instance, severity, summary, description)
                open_tickets[dedup_key] = {
                    "ticket_id": ticket_id,
                    "alertname": alertname,
                    "instance": instance,
                    "severity": severity,
                    "summary": summary
                }
                processed.append({
                    "dedup_key": dedup_key,
                    "action": "ticket_created",
                    "ticket_id": ticket_id
                })

        elif status == "resolved":
            if dedup_key in open_tickets:
                ticket_info = open_tickets.pop(dedup_key)
                print(f"[ALERT RESOLVED] {dedup_key} recovered. Closing ticket {ticket_info['ticket_id']}.", flush=True)
                processed.append({
                    "dedup_key": dedup_key,
                    "action": "ticket_resolved",
                    "ticket_id": ticket_info["ticket_id"]
                })
            else:
                print(f"[RESOLVED UNTRACKED] Received resolve event for untracked alert: {dedup_key}", flush=True)
                processed.append({
                    "dedup_key": dedup_key,
                    "action": "ignored_untracked"
                })

    return jsonify({"status": "processed", "results": processed}), 200

if __name__ == "__main__":
    print(f"[STARTUP] Starting Ticket Service on port {PORT}...", flush=True)
    print(f"[CONFIG] Jira Integration Active: {is_jira_configured()}", flush=True)
    app.run(host="0.0.0.0", port=PORT)
