import os
import sys
import time
import socket
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

# Bridges to monitor (name, host_port, internal_port)
FLEET = [
    {"name": "bridge-01", "port": 8001},
    {"name": "bridge-02", "port": 8002},
    {"name": "bridge-03", "port": 8003},
]

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
LOG_FILE = os.path.join(LOG_DIR, "autofix.log")

os.makedirs(LOG_DIR, exist_ok=True)

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def check_tcp_port(host, port, timeout=2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def check_http_health(url, timeout=3):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BrivoAutoFix/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.getcode() == 200
    except Exception:
        return False

def run_diagnostics(bridge_name, port):
    log_event(f"[DIAGNOSTICS] Running network triage for {bridge_name} on port {port}...")

    # 1. TCP Port probe
    port_open = check_tcp_port("127.0.0.1", port)
    log_event(f"[DIAGNOSTICS] TCP Probe 127.0.0.1:{port} -> {'OPEN' if port_open else 'CLOSED / UNREACHABLE'}")

    # 2. Local DNS resolution test
    try:
        ip = socket.gethostbyname("localhost")
        log_event(f"[DIAGNOSTICS] DNS check: 'localhost' resolved to {ip} (OK)")
    except Exception as e:
        log_event(f"[DIAGNOSTICS] DNS check failed: {e}")

    # 3. Docker container inspect
    try:
        out = subprocess.check_output(["docker", "inspect", "-f", "{{.State.Status}}", bridge_name], text=True).strip()
        log_event(f"[DIAGNOSTICS] Docker container state for {bridge_name}: '{out}'")
    except Exception as e:
        log_event(f"[DIAGNOSTICS] Docker inspect failed: {e}")

def remediate_bridge(bridge_name, port):
    log_event(f"[REMEDIATION] Attempting automated self-healing restart for {bridge_name}...")
    try:
        res = subprocess.run(["docker", "restart", bridge_name], capture_output=True, text=True, check=True)
        log_event(f"[REMEDIATION] Docker restart issued successfully for {bridge_name}. Output: {res.stdout.strip()}")
        
        # Verify post-restart health
        time.sleep(3)
        healthy = check_http_health(f"http://127.0.0.1:{port}/health")
        if healthy:
            log_event(f"[AUTO-FIX SUCCESS] {bridge_name} recovered and passing /health checks! Incident resolved.")
            return True
        else:
            log_event(f"[AUTO-FIX WARNING] {bridge_name} restarted but /health endpoint still failing. Escalating to Level 2 On-Call.")
            return False
    except subprocess.CalledProcessError as e:
        log_event(f"[AUTO-FIX FAILED] Could not restart {bridge_name}: {e.stderr.strip()}")
        return False

def audit_fleet():
    log_event("=" * 60)
    log_event("=== Brivo Operations Fleet Auto-Fix Scanner Started ===")
    issues_found = 0
    healed = 0

    for dev in FLEET:
        name = dev["name"]
        port = dev["port"]
        health_url = f"http://127.0.0.1:{port}/health"

        is_healthy = check_http_health(health_url)
        if is_healthy:
            log_event(f"[STATUS OK] {name} is healthy on port {port}.")
        else:
            issues_found += 1
            log_event(f"[ALERT TRIGGERED] {name} is DOWN or unresponsive on port {port}!")
            run_diagnostics(name, port)
            if remediate_bridge(name, port):
                healed += 1

    log_event(f"=== Scan Completed. Issues Found: {issues_found}, Auto-Healed: {healed} ===")
    log_event("=" * 60)
    return issues_found, healed

if __name__ == "__main__":
    audit_fleet()
