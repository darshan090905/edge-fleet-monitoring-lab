import os
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import start_http_server, Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST

# Configuration from Environment Variables
DEVICE_ID = os.getenv("DEVICE_ID", "bridge-01")
PORT = int(os.getenv("AGENT_PORT", "8000"))
START_TIME = time.time()

# Prometheus Metrics Definitions
DEVICE_STATUS = Gauge(
    "bridge_device_status",
    "Overall health status of the bridge device (1 = healthy, 0 = degraded)",
    ["device_id"]
)
CAMERAS_CONNECTED = Gauge(
    "bridge_camera_connected_count",
    "Number of IP cameras currently connected to this bridge",
    ["device_id"]
)
HEARTBEATS_TOTAL = Counter(
    "bridge_heartbeats_total",
    "Total heartbeat pulses sent by the bridge agent",
    ["device_id"]
)
LAST_HEARTBEAT_TIMESTAMP = Gauge(
    "bridge_last_heartbeat_timestamp_seconds",
    "Unix timestamp of the last successful heartbeat pulse",
    ["device_id"]
)

# Initialize starting values
DEVICE_STATUS.labels(device_id=DEVICE_ID).set(1)
CAMERAS_CONNECTED.labels(device_id=DEVICE_ID).set(2)
LAST_HEARTBEAT_TIMESTAMP.labels(device_id=DEVICE_ID).set(time.time())

class BridgeRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Update heartbeat metrics on each health/status check
        HEARTBEATS_TOTAL.labels(device_id=DEVICE_ID).inc()
        LAST_HEARTBEAT_TIMESTAMP.labels(device_id=DEVICE_ID).set(time.time())

        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = {
                "status": "healthy",
                "device_id": DEVICE_ID,
                "uptime_seconds": int(time.time() - START_TIME),
                "cameras_connected": 2,
                "firmware_version": "v1.4.2-brivo-edge"
            }
            self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))

        elif self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(generate_latest())

        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Clean terminal logging
        print(f"[{DEVICE_ID}] {self.address_string()} - {format % args}")

def run():
    print(f"[{DEVICE_ID}] Starting Bridge Agent on port {PORT}...")
    server = HTTPServer(("0.0.0.0", PORT), BridgeRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"[{DEVICE_ID}] Stopping Bridge Agent...")
        server.server_close()

if __name__ == "__main__":
    run()
