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

| # | Threat Capability |
|---|---|
| 1 | Volumetric / Protocol DDoS |
| 2 | Botnet C2 Beaconing |
| 3 | DGA / DNS Tunneling |
| 4 | Malware inside encrypted sessions |
| 5 | Reconnaissance / Port Scanning |
| 6 | Data Exfiltration |

### Detector Modules

| # | Detector Module |
|---|---|
| 1 | DDoS Detector |
| 2 | Recon Detector |
| 3 | DNS/DGA/DNS-Tunneling Detector |
| 4 | TLS/C2 Detector |
| 5 | Exfiltration Detector |

These are five logical modules — **not** five microservices.

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
│   ├── architecture/     # Architecture checkpoint (source of truth)
│   ├── data/             # Canonical Event Schema (source of truth)
│   ├── backend/          # Backend context + decisions
│   ├── frontend/         # Frontend context + decisions
│   └── shared/           # API contract, data contracts, integration notes
├── frontend/             # React + Vite + TypeScript (Dummy Shell)
├── backend/              # Python + FastAPI (Dummy API)
├── infra/                # Infrastructure configs
├── tests/                # Cross-cutting tests
├── AGENTS.md             # Agent rules and project reference
├── README.md             # This file
├── .gitignore
├── .env.example
└── docker-compose.yml
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

## Environment Setup

Before running the backend or frontend:

```bash
# Copy the environment template to create your local config
cp .env.example .env
```

Edit `.env` and fill in appropriate values. **Never commit `.env`** — it is gitignored.

---

## Backend Setup / Run (Dummy Phase)

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

# To run the FastAPI server (requires active Docker infrastructure):
uvicorn app.main:app --reload --port 8000

# To manually ingest a PCAP for detection (requires active Docker infrastructure):
# Note: Ensure Redpanda is accessible at localhost:19092
python run_prototype.py --pcap C:\path\to\your\traffic.pcap
```

---

## Frontend Setup / Run (Dummy Phase)

```bash
cd frontend
npm install
npm run dev
```

---

## References

- [Architecture Checkpoint](docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md)
- [Canonical Event Schema](docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md)
- [API Contract (Draft)](docs/shared/API_CONTRACT.md)
- [AGENTS.md](AGENTS.md)
