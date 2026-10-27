# Brivo Operations Lab - Incident & Failure Simulator
param (
    [Parameter(Position=0)]
    [ValidateSet("stop_bridge", "load_cpu", "fill_disk", "block_camera", "recover_all", "status")]
    [string]$Action = "status"
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Brivo Failure Simulator: $Action" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Cyan

switch ($Action) {
    "stop_bridge" {
        Write-Host "[FAILURE 1] Stopping edge bridge 'bridge-02'..." -ForegroundColor Red
        docker stop bridge-02
        Write-Host "Bridge-02 stopped! Watch Prometheus, Alertmanager, and Grafana." -ForegroundColor Green
    }

    "load_cpu" {
        Write-Host "[FAILURE 2] Inducing high CPU load on bridge-01..." -ForegroundColor Red
        docker exec -d bridge-01 python -c "import time; t = time.time() + 30; [x**2 for x in range(10**7)] while time.time() < t: pass"
        Write-Host "High CPU job launched inside bridge-01 for 30s! Check CPU telemetry in Grafana." -ForegroundColor Green
    }

    "fill_disk" {
        Write-Host "[FAILURE 3] Simulating critical disk fill inside bridge-03..." -ForegroundColor Red
        docker exec bridge-03 dd if=/dev/zero of=/app/simulated_large_log.dat bs=1M count=150
        Write-Host "Created 150MB log file inside bridge-03! Check HighDiskUsage alert." -ForegroundColor Green
    }

    "block_camera" {
        Write-Host "[FAILURE 4] Simulating RTSP Camera feed disconnect..." -ForegroundColor Red
        docker stop cam
        Write-Host "Camera container stopped! Check CameraStreamDown alert and Grafana." -ForegroundColor Green
    }

    "recover_all" {
        Write-Host "[RECOVERY] Restoring all services to healthy baseline..." -ForegroundColor Cyan
        docker start bridge-01 bridge-02 bridge-03 cam 2>$null
        docker exec bridge-03 rm -f /app/simulated_large_log.dat 2>$null
        docker compose up -d
        Write-Host "All edge bridges and camera feeds recovered!" -ForegroundColor Green
    }

    "status" {
        Write-Host "Usage: .\scripts\simulate_failure.ps1 <action>" -ForegroundColor White
        Write-Host "Available actions:"
        Write-Host "  stop_bridge   - Stops bridge-02 (Triggers BridgeDown alert & Jira ticket)"
        Write-Host "  load_cpu      - Spikes CPU on bridge-01"
        Write-Host "  fill_disk     - Fills storage on bridge-03"
        Write-Host "  block_camera  - Stops the RTSP camera feed (Triggers CameraStreamDown)"
        Write-Host "  recover_all   - Recovers all containers and cleans up disks"
    }
}
