# Vibhinetra — Continuous Live Streaming & Deployment Guide

## Overview

Vibhinetra includes a 24/7 continuous streaming telemetry generator designed for live deployments, demonstrations, and evaluation. It generates realistic multi-vector network traffic in an infinite loop, streaming events directly into Redpanda topics, which are immediately processed by backend detectors, published via Redis Pub/Sub, and rendered dynamically on the frontend dashboard.

---

## Architecture Flow

```
┌─────────────────────────────────┐
│ vibhinetra-traffic-generator    │ (Continuous Loop)
│ (scripts/live_demo.py)          │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Redpanda Event Topics           │
│ • vibhinetra.events.connection.v1
│ • vibhinetra.events.dns.v1      │
│ • vibhinetra.events.tls.v1      │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ vibhinetra-backend              │
│ • Feature Extraction Engine     │
│ • Multi-Vector Threat Detectors │ (DDoS, Exfil, C2, Recon, DNS, Unknown)
│ • Alert Scoring & Deduplication │
└───────────────┬─────────────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │ Redis PubSub │
│ (Persistence)│ │ (Real-Time)  │
└──────────────┘ └──────┬───────┘
                        │
                        ▼ (WebSocket)
┌─────────────────────────────────┐
│ vibhinetra-frontend             │
│ • Live Threat Posture Score     │
│ • Real-time Notification Bell   │
│ • Animated On-Screen Alert Toast│
└─────────────────────────────────┘
```

---

## 1. Automated Turnkey Deployment (Docker Compose)

The `docker-compose.yml` has been updated with a dedicated `traffic-generator` service that runs in an **infinite continuous loop** by default (`restart: unless-stopped`).

### Start the Entire Stack
```bash
docker compose up -d
```

This single command brings up:
1. `vibhinetra-postgres` — Relational storage
2. `vibhinetra-redis` — Ephemeral state & WebSocket Pub/Sub
3. `vibhinetra-redpanda` — Distributed event streaming
4. `vibhinetra-backend` — FastAPI detection pipeline
5. `vibhinetra-frontend` — React/Vite dashboard
6. `vibhinetra-traffic-generator` — **Continuous live traffic simulation**

### View Live Traffic Generator Logs
```bash
docker logs -f vibhinetra-traffic-generator
```

### Stop / Restart Traffic Generation
```bash
# Temporarily pause traffic simulation:
docker compose stop traffic-generator

# Resume traffic simulation:
docker compose start traffic-generator
```

---

## 2. Running Standalone (Host Terminal)

You can also run the streaming generator directly on the host machine using Python:

```powershell
cd D:\_Irochi_\Irochi\backend

# Run continuously in an infinite loop (default)
.venv\Scripts\python.exe scripts\live_demo.py

# Run for a specific duration (e.g., 10 minutes = 600s)
.venv\Scripts\python.exe scripts\live_demo.py --duration 600

# Fast tick rate (0.5s between batches)
.venv\Scripts\python.exe scripts\live_demo.py --tick 0.5
```

---

## 3. Replaying Captured Traffic Tape in a Loop

If you prefer replaying recorded network traffic (`data/real_demo_traffic.jsonl`) rather than procedural generation:

```powershell
# Continuous looping tape playback
.venv\Scripts\python.exe scripts\playback_demo.py --loop

# Adjust playback speed (e.g. 100 events per second)
.venv\Scripts\python.exe scripts\playback_demo.py --loop --rate 100
```

---

## 4. Configuration Options

Both scripts and Docker services can be customized via environment variables:

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `LOOP_FOREVER` | `true` | When `true`, loops indefinitely until stopped. |
| `DURATION_SECONDS` | `0` | `0` or negative means infinite loop; positive integer sets max runtime. |
| `TICK_INTERVAL` | `1.0` | Seconds between traffic generation bursts. |
| `REDPANDA_BROKER` | Auto-detect | Broker address (`redpanda:9092` inside Docker, `localhost:19092` outside). |

---

## 5. Traffic & Threat Scenarios Emitted

The continuous generator automatically alternates between benign traffic and multi-stage cyber threats:

- **Benign Baseline**: Continuous internal/external client-server connections and trusted TLS sessions (GitHub, Cloudflare, Microsoft, AWS).
- **C2 Beaconing**: Highly periodic heartbeats from compromised internal hosts (`192.168.1.15`, `192.168.1.22`) to known attacker command-and-control servers.
- **DGA / DNS Tunneling**: High-entropy pseudo-random domain queries targeting public DNS resolvers.
- **Port Reconnaissance**: Rapid multi-port SYN sweeps across common service ports (21, 22, 80, 443, 3389, 8080).
- **Data Exfiltration Spikes**: Periodic multi-megabyte outbound data bursts to external exfiltration sinks.
- **Volumetric DDoS Bursts**: High-frequency connection flood attacks from distributed botnet IP ranges.
