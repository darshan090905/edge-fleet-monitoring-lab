# Edge Device Fleet Monitoring & Auto-Troubleshooting Lab

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Prometheus](https://img.shields.io/badge/Prometheus-v2.51.0-E6522C?logo=prometheus&logoColor=white)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/Grafana-v10.4.1-F46800?logo=grafana&logoColor=white)](https://grafana.com/)
[![Jira](https://img.shields.io/badge/Atlassian-Jira%20Cloud-0052CC?logo=jira&logoColor=white)](https://www.atlassian.com/software/jira)
[![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20CloudWatch%20%7C%20SNS-232F3E?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Terraform](https://img.shields.io/badge/Terraform-v1.5+-844FBA?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Edge%20AI-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)

An enterprise-grade operations and telemetry engineering lab designed for **distributed edge fleet monitoring, cloud video surveillance, and automated IoT access control systems**. 

This project simulates a distributed edge fleet of Linux bridge devices connecting IP cameras to the cloud. It features real-time synthetic RTSP video streaming, edge computer vision people counting with strict zero-retention privacy guarantees, proactive Prometheus/Alertmanager monitoring, automated Atlassian Jira Cloud incident ticketing with alert deduplication, an autonomous Python self-healing script, and Terraform Infrastructure as Code (IaC) deployed to AWS EC2 with CloudWatch metric alarms and SNS email notifications.

---

## 🏛️ Architecture Overview

```mermaid
flowchart TB
    subgraph OnPremises["On-Premises Edge Fleet - Simulated IoT Devices"]
        subgraph Bridges["Linux Edge Bridge Fleet"]
            B1["bridge-01<br/>Agent :8001 | NodeExporter :9101"]
            B2["bridge-02<br/>Agent :8002 | NodeExporter :9102"]
            B3["bridge-03<br/>Agent :8003 | NodeExporter :9103"]
        end

        CAM["Synthetic IP Camera<br/>MediaMTX + ffmpeg RTSP :8554"]
        AI["Edge AI Container<br/>OpenCV HOG People Counter :8005"]

        CAM -->|RTSP Stream| AI
        CAM -.->|RTSP Feed| Bridges
    end

    subgraph TelemetryStack["Telemetry and Monitoring Core"]
        BB["Blackbox Exporter :9115<br/>TCP and HTTP Probing"]
        PROM["Prometheus v2.51.0 :9090<br/>Metrics Scraping and Rules"]
        AM["Alertmanager v0.27.0 :9093<br/>Incident Grouping and Routing"]
        GRAF["Grafana v10.4.1 :3000<br/>Auto-Provisioned Dashboards"]

        Bridges -->|Scrape System and Health| PROM
        CAM -->|TCP Probe 8554| BB
        Bridges -->|HTTP 200 Probe| BB
        AI -->|Inference Latency and Counts| PROM
        BB --> PROM
        PROM -->|PromQL Telemetry| GRAF
        PROM -->|Alert Events Above Threshold| AM
    end

    subgraph OpsAutomation["Operations and Incident Remediation"]
        TS["Flask Ticket Service :5001<br/>In-Memory Deduplication Engine"]
        JIRA["Atlassian Jira Cloud<br/>REST API v3 Issue Tracker"]
        AUTOF["Autonomous Self-Healing<br/>scripts/auto_fix.py"]

        AM -->|Webhook POST /alert| TS
        TS -->|Create Task Issue| JIRA
        AUTOF -->|Triage, Diagnose and Restart| Bridges
    end

    subgraph CloudInfra["AWS Cloud Infrastructure - Terraform"]
        EC2["EC2 t3.micro - Amazon Linux 2023<br/>2GB Swap + Docker Engine"]
        CW["CloudWatch Metric Alarms<br/>StatusCheckFailed and CPU > 80%"]
        SNS["Amazon SNS Topic<br/>Critical Email Notifications"]

        EC2 --> CW --> SNS
    end
```

---

## 📸 Live Operational Evidence & Screenshots

### 1. Unified Fleet & Edge AI Grafana Dashboard
*Displays real-time device health across all 3 bridges, RTSP camera stream reachability, total heartbeats, live edge computer vision inference latency (~187ms), and system CPU/Memory utilization.*

![Grafana Dashboard](docs/screenshots/01-grafana-dashboard.png)

---

### 2. Automated Atlassian Jira Cloud Incident Management
*When a bridge fails, Alertmanager triggers our Flask ticket microservice via webhook. The service performs alert deduplication and programmatically opens an incident task in Jira Cloud with full diagnostic details.*

![Jira Incident Ticket](docs/screenshots/02-jira-ticket.png)

---

### 3. Prometheus Alerting Rules Engine
*Evaluates threshold breaches (`BridgeDown`, `CameraStreamDown`, `HighDiskUsage`, `HighCPU`, `AIDetectorNoFrames`) every 5 seconds with hysteresis timing to prevent false alarms.*

![Prometheus Alerts](docs/screenshots/03-prometheus-alerts.png)

---

### 4. Autonomous Self-Healing Diagnostic Audit Trail
*The Python triage script detects unresponsive ports, verifies local DNS, inspects Docker container state, executes a safe automated restart, and records the resolution audit trail in `docs/autofix.log`.*

![Auto-Fix Audit Trail](docs/screenshots/04-autofix-log.png)

---

### 5. AWS Cloud Infrastructure (EC2 Control Center)
*Deployed via Terraform (`ap-southeast-2`) on an Amazon Linux 2023 `t3.micro` instance with 2GB swap space to host the remote control center.*

![AWS EC2 Console](docs/screenshots/05-aws-ec2-console.png)

---

### 6. CloudWatch Metric Alarm & SNS Email Warning
*Real-time CloudWatch alarm triggering an Amazon SNS alert email directly to the Operations Engineer when CPU utilization breaches 80%.*

![CloudWatch SNS Email Alert](docs/screenshots/06-cloudwatch-sns-email.png)

---

## 🚀 Key Architectural Capabilities

| Component | Technology | Operational Function |
|---|---|---|
| **Edge Fleet** | Docker, Python 3.11, Debian | 3 simulated edge appliances running Node Exporter and internal `/health` agents |
| **Video Ingestion** | MediaMTX, ffmpeg, RTSP | Broadcasts synthetic live camera video stream over RTSP port 8554 |
| **Edge AI Vision** | OpenCV HOG Descriptor, NumPy | Detects human silhouettes in volatile RAM without saving frames to disk |
| **Blackbox Probing**| Prometheus Blackbox Exporter | Probes TCP streaming ports (8554) and HTTP endpoints from the outside |
| **Metrics & Alerts**| Prometheus & Alertmanager | Scrapes targets every 5s; manages alert deduplication, grouping, and silencing |
| **Visualization**   | Grafana 10.4.1 | Provisioned dashboards with fleet status, memory/CPU gauges, and AI metrics |
| **Incident Ticketing**| Flask, Jira Cloud REST API v3| Ingests Alertmanager webhooks and generates deduplicated Jira tickets |
| **Auto-Remediation**| Python, Docker API | Triage script probing ports and DNS before triggering container recovery |
| **Cloud IaC**       | Terraform, AWS EC2, CloudWatch, SNS | Automated provisioning of Free Tier cloud host with email alerts |

---

## 🔒 Edge AI Privacy Guarantee

> [!NOTE]
> **Strict Zero-Retention Policy:**
> * **Volatile Processing Only:** Video frames are decoded into RAM buffers, analyzed for human silhouette contours via OpenCV's Histogram of Oriented Gradients (HOG) algorithm, and instantly discarded.
> * **Zero Video Retention:** No video streams, clips, or still frames are ever written to disk or transmitted off-device.
> * **No Facial Recognition:** The detector outputs integer silhouette count metrics only (`people_count`). No biometric identification or facial feature analysis is performed.

---

## 🛠️ Quickstart (Local Fleet)

### 1. Prerequisites
* Docker Desktop & Docker Compose v2+
* Python 3.10+
* Git

### 2. Clone & Run
```bash
git clone https://github.com/<your-username>/edge-fleet-monitoring-lab.git
cd edge-fleet-monitoring-lab

# Copy and customize environment variables
cp .env.example .env

# Launch all 10 microservices
docker compose up -d
```

### 3. Service Port Mapping
* **Grafana Dashboard:** [http://localhost:3000](http://localhost:3000) *(User: `admin`, Pass: `admin`)*
* **Prometheus Targets:** [http://localhost:9090/targets](http://localhost:9090/targets)
* **Prometheus Alert Rules:** [http://localhost:9090/alerts](http://localhost:9090/alerts)
* **Alertmanager Console:** [http://localhost:9093](http://localhost:9093)
* **Ticket Service Health:** [http://localhost:5001/health](http://localhost:5001/health)
* **RTSP Video Feed:** `rtsp://localhost:8554/cam`

---

## 🧪 Failure Simulation & Automated Healing

### Step 1: Simulate Edge Device Crash
```powershell
# Stops bridge-02 to simulate hardware failure
.\scripts\simulate_failure.ps1 stop_bridge
```
* **Prometheus:** `up{job="bridge_agents"} == 0` turns yellow (`Pending`) then red (`Firing`).
* **Alertmanager:** Dispatches webhook to `ticket-service:5001/alert`.
* **Jira Cloud:** Automatically creates an incident ticket (e.g., `SCRUM-6`).

### Step 2: Trigger Self-Healing Script
```powershell
python scripts/auto_fix.py
```
* Runs network triage (TCP probe, local DNS check, Docker inspect).
* Restarts `bridge-02` automatically.
* Alertmanager detects recovery and dispatches a `resolved` payload, closing the ticket lifecycle.
* Audit trail saved to [`docs/autofix.log`](docs/autofix.log).

---

## ☁️ AWS Cloud Infrastructure (Terraform)

Deploy the control center to AWS EC2:

```bash
cd terraform

# Initialize and preview
terraform init
terraform plan

# Apply infrastructure
terraform apply -auto-approve

# Clean up to guarantee $0 spend
terraform destroy -auto-approve
```

---

## 📖 Operations Runbook

For Level 1 / Level 2 Operations Engineers responding to fleet alerts, consult our detailed Standard Operating Procedures (SOP) in:
👉 **[docs/runbook.md](docs/runbook.md)**

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
