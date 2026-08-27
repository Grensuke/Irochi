# Irochi

**SIH 2026 — Problem Statement SIH26145**

Passive, real-time network threat-detection and security-intelligence system.

---

## Current Status

> **CURRENT: Dummy / scaffold implementation**
>
> The repository contains workflow structure, documentation, and placeholder directories.
> Backend and frontend skeletons are not yet implemented.

> **FUTURE: Real streaming / ML / security pipeline**
>
> Zeek → Normalizer → Redpanda → Feature Processing → Detectors → Alert Engine → PostgreSQL → Redis Pub/Sub → FastAPI → WebSocket → React Dashboard

---

## Project Purpose

Irochi is a passive, real-time network threat-detection system that:

- Observes network traffic through Zeek and NetFlow/IPFIX
- Normalizes telemetry into a source-independent canonical format
- Streams events through Redpanda for processing
- Extracts behavioural features and applies threat-specific detectors
- Generates scored, explainable security alerts
- Persists alerts to PostgreSQL as the durable source of truth
- Delivers live alerts to analysts via a WebSocket-powered React dashboard

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

```
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

```
Irochi/
├── .agents/              # Antigravity skills
├── docs/
│   ├── architecture/     # Architecture checkpoint (source of truth)
│   ├── data/             # Canonical Event Schema (source of truth)
│   ├── backend/          # Backend context + decisions
│   ├── frontend/         # Frontend context + decisions
│   └── shared/           # API contract, data contracts, integration notes
├── frontend/             # React + Vite + TypeScript (not yet created)
├── backend/              # Python + FastAPI (not yet created)
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

## Dummy vs Real Implementation

### Current (Dummy)

- Repository structure and documentation
- (Upcoming) FastAPI skeleton with mock endpoints
- (Upcoming) React dashboard with mock data
- (Upcoming) Simulated WebSocket with mock backfill + live alerts
- No real Zeek, Redpanda, Redis, PostgreSQL, or ML

### Future (Real)

- Zeek live capture / tcpreplay
- Python Ingest Normalizer producing canonical events
- Redpanda streaming
- Feature/window extraction
- Threat-specific ML detectors (Scikit-learn, XGBoost, River)
- PostgreSQL persistence
- Redis hot state + Pub/Sub
- JWT/RBAC authentication
- Production Docker Compose environment

---

## Environment Setup

Before running the backend, frontend, or Docker Compose:

```bash
# Copy the environment template to create your local config
cp .env.example .env
```

Edit `.env` and fill in appropriate values. **Never commit `.env`** — it is gitignored. Only `.env.example` (the template) is tracked in version control.

---

## Backend Setup / Run

> _Not yet implemented — will be added in Checkpoint 2._


```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## Frontend Setup / Run

> _Not yet implemented — will be added in Checkpoint 3._

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
