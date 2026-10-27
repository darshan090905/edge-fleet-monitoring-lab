# Operations Runbook: Brivo Edge Fleet & Surveillance Systems

> **Target Audience:** Brivo Operations Engineers, On-Call Site Reliability Engineers  
> **System:** Distributed Edge Device Fleet & Cloud Surveillance Control Center

---

## Quick Reference Table

| Alert Name | Severity | Primary Root Cause | First Action | SLA / Response Time |
|---|---|---|---|---|
| **BridgeDown** | Critical | Device offline / Agent crashed / Power loss | Run `scripts/auto_fix.py` or `docker restart <bridge>` | 15 minutes |
| **CameraStreamDown** | Critical | RTSP feed lost / Network cable cut | Check camera IP & restart `cam` service | 15 minutes |
| **HighDiskUsage** | Warning | Log rotation failed / Core dumps accumulating | Clean `/tmp` and rotate `/var/log` | 1 hour |
| **HighCPU** | Warning | Runaway process / HOG inference overload | Check `top` inside bridge / Throttle FPS | 30 minutes |
| **AIDetectorNoFrames** | Warning | Stream stalled / OpenCV buffer frozen | Restart `edge-ai` container | 30 minutes |

---

## 1. Alert: `BridgeDown`

### Summary & Meaning
An on-premise Linux bridge (`bridge-01`, `bridge-02`, or `bridge-03`) has stopped responding to both Prometheus scraping and `/health` heartbeats for more than 10 seconds.

### Customer / Business Impact
Access control readers and IP cameras routed through this bridge cannot relay events or video recordings to the Brivo Cloud. Doors may be in fail-safe/fail-secure mode.

### Triage & Diagnostic Steps
1. Verify bridge container status:
   ```bash
   docker ps -a --filter "name=bridge"
   ```
2. Probe TCP connectivity and health endpoint directly:
   ```bash
   curl -I http://localhost:8001/health   # for bridge-01
   curl -I http://localhost:8002/health   # for bridge-02
   curl -I http://localhost:8003/health   # for bridge-03
   ```
3. Inspect container logs for crash traces:
   ```bash
   docker logs --tail 50 bridge-02
   ```

### Remediation Steps
1. **Automated Fix:** Run the self-healing runner:
   ```bash
   python scripts/auto_fix.py
   ```
2. **Manual Fix:** If container exited, restart it:
   ```bash
   docker restart bridge-02
   ```
3. If container starts but health check fails, open an interactive bash shell to troubleshoot internal processes:
   ```bash
   docker exec -it bridge-02 ps aux
   docker exec -it bridge-02 curl http://localhost:8000/health
   ```

---

## 2. Alert: `CameraStreamDown`

### Summary & Meaning
Prometheus Blackbox Exporter failed to establish a TCP handshake on port `8554` (RTSP) against the camera stream server (`cam:8554`).

### Customer / Business Impact
No live video or recordings can be viewed by building security staff or ingested by computer vision analytics.

### Triage & Diagnostic Steps
1. Test TCP port reachability:
   ```bash
   nc -zv localhost 8554
   # Or in PowerShell:
   Test-NetConnection -ComputerName localhost -Port 8554
   ```
2. Check MediaMTX container status and logs:
   ```bash
   docker logs --tail 40 cam
   ```

### Remediation Steps
1. Restart the RTSP streaming engine:
   ```bash
   docker restart cam
   ```
2. Verify stream re-advertisement:
   ```bash
   curl -I http://localhost:8554
   ```

---

## 3. Alert: `HighDiskUsage`

### Summary & Meaning
The root partition filesystem usage on an edge bridge has exceeded 85% capacity.

### Customer / Business Impact
If storage reaches 100%, the bridge operating system will fail to write SQLite locks, local video caches, and telemetry logs, causing complete bridge failure.

### Triage & Diagnostic Steps
1. Check filesystem free space:
   ```bash
   docker exec -it bridge-03 df -h /
   ```
2. Locate the largest files:
   ```bash
   docker exec -it bridge-03 du -ah /app | sort -rh | head -n 10
   ```

### Remediation Steps
1. Delete temporary diagnostic files or simulated large files:
   ```bash
   docker exec -it bridge-03 rm -f /app/*.dat /app/*.log
   ```
2. If disk usage was filled via the failure simulator:
   ```powershell
   .\scripts\simulate_failure.ps1 recover_all
   ```

---

## 4. Alert: `HighCPU`

### Summary & Meaning
Average CPU utilization across the bridge device has exceeded 90% continuously for 5 minutes.

### Customer / Business Impact
High latency on door unlock commands and frame dropping on video ingestion.

### Triage & Diagnostic Steps
1. Check running processes inside the bridge:
   ```bash
   docker exec -it bridge-01 top -b -n 1
   ```
2. Identify process PID consuming excessive CPU.

### Remediation Steps
1. Terminate runaway or rogue processes:
   ```bash
   docker exec -it bridge-01 pkill -9 -f "python -c"
   ```
2. Restart the bridge if necessary:
   ```bash
   docker restart bridge-01
   ```

---

## 5. Alert: `AIDetectorNoFrames`

### Summary & Meaning
The `edge-ai` computer vision pipeline has processed 0 video frames over a 2-minute rolling window (`rate(frames_processed_total[2m]) == 0`).

### Customer / Business Impact
People counting and building occupancy telemetry are inactive, impacting automated capacity and occupancy dashboards.

### Triage & Diagnostic Steps
1. Check Edge AI container logs:
   ```bash
   docker logs --tail 30 edge-ai
   ```
2. Check if the camera stream is still alive:
   ```bash
   docker ps --filter "name=cam"
   ```

### Remediation Steps
1. Restart the `edge-ai` container to re-initialize the OpenCV video capture pipeline:
   ```bash
   docker restart edge-ai
   ```
2. Verify metrics resume incrementing:
   ```bash
   curl -s http://localhost:8005/metrics | grep frames_processed_total
   ```
