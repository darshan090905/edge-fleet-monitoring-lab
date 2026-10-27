#!/bin/sh
set -e

echo "[BRIDGE INIT] Starting Node Exporter on port 9100..."
/usr/local/bin/node_exporter --web.listen-address=":9100" &

echo "[BRIDGE INIT] Starting Bridge Agent on port 8000..."
exec python /app/agent.py
