# Irochi

**SIH 2026 — Problem Statement SIH26145**

**Problem Statement Title:** AI-Based Detection of Cyber Threats in Unidirectional IP Traffic

Passive, real-time network threat-detection and security-intelligence system.

---

## Current Status

> **CURRENT: Checkpoint 4 (FINAL DUMMY END-TO-END INTEGRATION)**
>
> The repository contains a complete, verified dummy end-to-end application.
> - **Backend:** FastAPI skeleton with mock data endpoints and simulated WebSocket live alerts.
> - **Frontend:** Complete React + Vite product shell with dummy integration.
>
> **This is NOT the real SIH26145 production pipeline yet.** No real Zeek, Redpanda, PostgreSQL, or ML is implemented in this dummy phase.

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
uvicorn app.main:app --reload --port 8000
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
