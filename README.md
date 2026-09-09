# Irochi

**SIH 2026 — Problem Statement SIH26145**

**Problem Statement Title:** AI-Based Detection of Cyber Threats in Unidirectional IP Traffic

Passive, real-time network threat-detection and security-intelligence system.

---

## Current Status

> **CURRENT: Active Infrastructure & Detector Evaluation Phase**
>
> The repository contains a fully integrated pipeline with active infrastructure.
> - **Backend:** FastAPI with `DetectionPipeline` consuming from Redpanda, routing to active detectors, saving to PostgreSQL, and streaming via Redis Pub/Sub to real REST/WebSocket endpoints.
> - **Frontend:** React + Vite product shell. The alerts integration uses the *real* API, while other telemetry dashboards remain in a demo state.
> - **Evaluation:** Extensive detector evaluation tooling (Level 1 & Level 2 methodology using CIC-IDS2017) has been implemented and run to establish baselines.
>
> **Active Detectors & Defaults:**
> - DDoS Detector (default threshold: 1000 pps)
> - Recon Detector (default threshold: 50 ports)
> - DNS/DGA Detector (Requires external `.joblib` model artifact)
>
> **Known Limitations:**
> Evaluation has shown severe limitations with the current flow-window distortion and default thresholds (e.g., 1000 pps misses low-bandwidth DoS). These default thresholds remain active but candidate improvements are documented. DGA relies on an external model artifact.

---

## Project Purpose & Design Philosophy

Irochi is a passive, real-time network threat-detection system. It is strictly designed for:

- **Passive observation** of one-directional IP traffic
- **Read-only ingest** (via Zeek and NetFlow/IPFIX)
- **No return path** into the production network
- **No active probing**
- **No mitigation or blocking action**
- **No payload decryption** (TLS/metadata analysis only)
- **Incremental/streaming processing**
- **Near-real-time detection and alerting**

Irochi is an intelligence system. It produces:
- **Labelled alerts**
- **Confidence scores**
- **Supporting evidence**

**Irochi does NOT claim to mitigate the detected threat.** Alerts are provided to security analysts for review (with states like New, Investigating, Closed, and False Positive).

### Threat Capabilities

| # | Threat Capability | Status |
|---|---|---|
| 1 | Volumetric / Protocol DDoS | **Active** |
| 2 | Botnet C2 Beaconing | Planned |
| 3 | DGA / DNS Tunneling | **Active** (Requires ML Model) |
| 4 | Malware inside encrypted sessions | Planned |
| 5 | Reconnaissance / Port Scanning | **Active** |
| 6 | Data Exfiltration | Planned |

### Detector Modules

| # | Detector Module | Status |
|---|---|---|
| 1 | DDoS Detector | **Active** |
| 2 | Recon Detector | **Active** |
| 3 | DNS/DGA/DNS-Tunneling Detector | **Active** (Requires `.joblib`) |
| 4 | TLS/C2 Detector | Planned |
| 5 | Exfiltration Detector | Planned |

These are logical modules — **not** microservices.

---

## High-Level Architecture

```text
PCAP / Live Packets ─────→ Zeek ─────→ Zeek Logs
                                            │
NetFlow / IPFIX ────────────────────────────┤
                                            ↓
                                    Ingest Normalizer
                                            ↓
                                        Redpanda
                                            ↓
                                    Feature Processing
                                            ↓
                                        Detectors
                                            ↓
                                      Alert Engine
                                            ↓
                                    PostgreSQL INSERT
                                            ↓
                                      AWAIT COMMIT
                                            ↓
                                    Redis Pub/Sub
                                            ↓
                                   FastAPI WebSocket
                                            ↓
                                    React Dashboard
```

See: [`docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md`](docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md)

---

## Repository Structure

```text
Irochi/
├── .agents/              # Antigravity skills
├── docs/
│   ├── architecture/     # Architecture checkpoints (source of truth)
│   ├── data/             # Canonical Event Schema (source of truth)
│   ├── backend/          # Backend context + decisions
│   ├── frontend/         # Frontend context + decisions
│   └── shared/           # API contract, data contracts, integration notes
├── frontend/             # React + Vite + TypeScript
├── backend/              # Python + FastAPI
│   ├── app/              # Application source
│   ├── tests/            # Automated tests
│   └── tools/            # Offline evaluation and diagnostic tools
├── infra/                # Infrastructure configs (future/Zeek)
├── AGENTS.md             # Agent rules and project reference
├── README.md             # This file
├── .gitignore
├── .env.example
└── docker-compose.yml    # Root Docker Compose for backend, frontend, DBs
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + TypeScript |
| Backend | Python + FastAPI |
| Network Telemetry | Zeek + Python Ingest Normalizer |
| Streaming | Redpanda |
| AI/ML | Scikit-learn + XGBoost + River |
| Hot State | In-memory + Redis |
| Persistent Storage | PostgreSQL |
| Real-time | WebSockets |
| Security | JWT + RBAC + Argon2 |
| Infrastructure | Docker + Docker Compose |
| Observability | Structured JSON Logging + Prometheus + Grafana |

---

## Environment Setup & Configuration

Before running any services, set up your local environment configuration:

```bash
# Copy the environment template
cp .env.example .env
```

Edit `.env` and fill in appropriate values. **Never commit `.env`**.

### Important Network Configurations
When running the stack, pay attention to Redpanda connectivity depending on where the producer/consumer is running:
- **From within Docker (e.g. FastAPI Backend)**: Connect to Redpanda using `REDPANDA_BROKER=redpanda:9092`
- **From Host Machine (e.g. PCAP Runner script)**: Connect to Redpanda using `localhost:19092`

---

## Running the Application (Docker Workflow)

The recommended way to run Irochi is using the root `docker-compose.yml`. This spins up the active infrastructure (PostgreSQL, Redis, Redpanda) alongside the FastAPI backend and React frontend.

```bash
docker compose up --build
```
- Frontend available at: `http://localhost:5173`
- Backend API available at: `http://localhost:8000`

### Ingesting Traffic (Host PCAP Runner)
To manually ingest a PCAP file for detection while the Docker stack is running:

```bash
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt

# Run the prototype ingestor from the host machine (targets localhost:19092)
python run_prototype.py --pcap C:\path\to\your\traffic.pcap
```

---

## References

- [Architecture Checkpoint](docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md)
- [Canonical Event Schema](docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md)
- [API Contract (Draft)](docs/shared/API_CONTRACT.md)
- [Evaluation](docs/EVALUATION.md)
- [AGENTS.md](AGENTS.md)
