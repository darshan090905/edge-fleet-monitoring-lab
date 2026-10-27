#!/bin/bash
# Brivo Operations Lab - Incident & Failure Simulator (Bash)

ACTION=${1:-status}

echo "========================================="
echo "   Brivo Failure Simulator: $ACTION"
echo "========================================="

case $ACTION in
    stop_bridge)
        echo "[FAILURE 1] Stopping edge bridge 'bridge-02'..."
        docker stop bridge-02
        echo "Bridge-02 stopped! Watch Prometheus, Alertmanager, and Grafana."
        ;;
    load_cpu)
        echo "[FAILURE 2] Inducing high CPU load on bridge-01..."
        docker exec -d bridge-01 python -c "import time; t = time.time() + 30; [x**2 for x in range(10**7)] while time.time() < t: pass"
        echo "High CPU job launched inside bridge-01 for 30s! Check Grafana."
        ;;
    fill_disk)
        echo "[FAILURE 3] Simulating critical disk fill inside bridge-03..."
        docker exec bridge-03 dd if=/dev/zero of=/app/simulated_large_log.dat bs=1M count=150
        echo "Created 150MB log file inside bridge-03! Check HighDiskUsage alert."
        ;;
    block_camera)
        echo "[FAILURE 4] Simulating RTSP Camera feed disconnect..."
        docker stop cam
        echo "Camera container stopped! Check CameraStreamDown alert and Grafana."
        ;;
    recover_all)
        echo "[RECOVERY] Restoring all services to healthy baseline..."
        docker start bridge-01 bridge-02 bridge-03 cam 2>/dev/null
        docker exec bridge-03 rm -f /app/simulated_large_log.dat 2>/dev/null
        docker compose up -d
        echo "All edge bridges and camera feeds recovered!"
        ;;
    *)
        echo "Usage: ./scripts/simulate_failure.sh <action>"
        echo "Available actions: stop_bridge | load_cpu | fill_disk | block_camera | recover_all"
        ;;
esac
