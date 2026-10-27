# Stage 1: Get official stable node_exporter binary
FROM prom/node-exporter:v1.8.0 AS node_exporter_bin

# Stage 2: Bridge Edge OS container
FROM python:3.11-slim

# Install system utilities used by Operations Engineers during incident troubleshooting
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    net-tools \
    iputils-ping \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Copy node_exporter binary from Stage 1
COPY --from=node_exporter_bin /bin/node_exporter /usr/local/bin/node_exporter

WORKDIR /app

# Install Python Prometheus client
RUN pip install --no-cache-dir prometheus-client

# Copy application files
COPY agent.py /app/agent.py
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Port 8000: Bridge Agent (/health & custom /metrics)
# Port 9100: Node Exporter (System CPU, RAM, Disk, Network)
EXPOSE 8000 9100

ENTRYPOINT ["/app/entrypoint.sh"]
