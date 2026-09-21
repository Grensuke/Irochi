# Irochi

**SIH 2026 — Problem Statement SIH26145**

**Problem Statement Title:** AI-Based Detection of Cyber Threats in Unidirectional IP Traffic

Irochi is a passive, real-time network threat-detection and security-intelligence system for unidirectional IP traffic.

---

## Current Status

> **Phase: Active Detection & Incident Correlation**
>
> The system has a fully operational detection pipeline backed by real infrastructure. The frontend connects to a live backend via REST and WebSockets.
>
> **What is live:**
> - All 6 detector modules are active and producing alerts
> - Alerts persist to PostgreSQL and stream via Redis Pub/Sub → WebSocket → React dashboard
> - Incident Engine groups correlated alerts into multi-stage incidents
> - Anomaly Detector runs Z-Score / Isolation Forest baseline analysis
> - AI Narrative Engine generates human-readable summaries for analysts
> - PCAP-based live demo pipeline is functional (`backend/scripts/live_demo.py`)
> - **NEW:** Active telemetry hardware simulations for passive diodes using HTML5 Canvas (`DiodeFlowVisualizer`, `UnidirectionalThreatStream`)
> - **NEW:** Advanced Incident Investigation Queue UI with risk scores and visual phase indicators
> - **NEW:** Client-side "Export to PDF" reporting capability integrated with AI narratives
>
> **Known limitations:**
> - DNS/DGA detector requires an external `.joblib` model artifact at startup
> - Window duration and threshold tuning is ongoing (see evaluation docs)
> - TimescaleDB is not yet enabled (conditional decision, not locked)

---

## What Irochi Is (and Is Not)

Irochi is a **passive intelligence system**. It strictly:

- Observes unidirectional IP traffic passively
- Normalises traffic from multiple sources (Zeek logs, NetFlow/IPFIX)
- Detects and classifies cyber threats with confidence scores
- Produces labelled security alerts with supporting evidence
- Clusters related alerts into incidents for analyst workflow
- Delivers alerts live to a React security dashboard via WebSockets

Irochi does **NOT**:
- Probe or contact traffic sources/destinations
- Decrypt TLS/QUIC payloads
- Send mitigation or blocking commands
- Act inline on production network traffic

> **"Closed" is an analyst workflow status.** It does not mean Irochi blocked or mitigated the threat.

---

## Threat Capabilities

| # | Threat Capability | Detector Module | Status |
|---|---|---|---|
| 1 | Volumetric / Protocol DDoS | DDoS Detector | **Active** |
| 2 | Reconnaissance / Port Scanning | Recon Detector | **Active** |
| 3 | DGA / DNS Tunneling | DNS/DGA/Tunnel Detector | **Active** (requires `.joblib`) |
| 4 | Botnet C2 Beaconing | TLS/C2 Detector | **Active** |
| 5 | Malware inside encrypted sessions | TLS/C2 Detector | **Active** |
| 6 | Data Exfiltration | Exfiltration Detector | **Active** |
| 7 | Novel Anomaly / Baseline Deviation | Anomaly Detector | **Active** |

---

## Detector Modules

There are **six logical detector modules** — not six microservices. Each module may emit one or more threat types.

| # | Module | Threat Types Emitted |
|---|---|---|
| 1 | DDoS Detector | `volumetric_ddos` |
| 2 | Recon Detector | `recon_portscan` |
| 3 | DNS/DGA/Tunnel Detector | `dga_dns_tunnel` |
| 4 | TLS/C2 Detector | `c2_beaconing`, `encrypted_malware` |
| 5 | Exfiltration Detector | `data_exfiltration` |
| 6 | Unknown Detector | `unknown_threat` |

---

## High-Level Architecture

```
PCAP / Live Packets --> Zeek --> Zeek Logs (conn / dns / ssl)
                                        |
NetFlow / IPFIX ────────────────────────┤
                                        v
                               Ingest Normalizer
                                        v
                                    Redpanda
                                        v
                              Feature Processing
                              (in-memory + Redis)
                                        v
              +─────────────────────────────────────────+
              |               Detectors                 |
              |  DDoS | Recon | DNS | TLS/C2 |          |
              |             Exfil | Anomaly             |
              +─────────────────────────────────────────+
                                        v
                                  Alert Engine
                                        v
                            PostgreSQL INSERT / UPDATE
                                        v
                                  AWAIT COMMIT
                                        v
                              Incident Engine
                          (cluster correlated alerts)
                                        v
                               Redis Pub/Sub
                                        v
                             FastAPI WebSocket
                                        v
                              React Dashboard
```

See [`docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md`](docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md) for the full annotated architecture.

---

## Repository Structure

```
Irochi/
├── .agents/              # Antigravity agent skills
├── docs/
│   ├── architecture/     # Architecture checkpoint + schema drafts (source of truth)
│   ├── data/             # Canonical Event Schema (source of truth)
│   ├── backend/          # Backend context + decisions
│   ├── frontend/         # Frontend context + decisions
│   └── shared/           # API contract, data contracts, integration notes
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes + WebSocket handlers
│   │   ├── core/         # Config, security, DB connections
│   │   ├── models/       # SQLAlchemy ORM models (Alert, Incident)
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   └── services/
│   │       ├── detectors/    # 6 detector modules + router + registry
│   │       ├── features/     # Feature extraction
│   │       ├── ingest/       # Ingest normalizer
│   │       ├── state/        # Hot state management
│   │       ├── streaming/    # Redpanda consumer
│   │       ├── alert_engine.py
│   │       ├── incident_engine.py
│   │       ├── ai_narrative.py
│   │       ├── postgres_alert_service.py
│   │       ├── postgres_incident_service.py
│   │       └── redis_pubsub.py
│   ├── scripts/          # Live demo + PCAP runner scripts
│   ├── tests/            # Automated tests
│   └── requirements.txt
├── frontend/             # React + Vite + TypeScript
├── infra/                # Infrastructure configs (Zeek)
├── models/               # ML model artifacts (.joblib)
├── AGENTS.md             # Agent governance rules
├── README.md             # This file
├── .env.example          # Environment variable template
└── docker-compose.yml    # Full stack orchestration
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + TypeScript |
| Backend | Python + FastAPI |
| Network Telemetry | Zeek + Python Ingest Normalizer |
| Streaming | Redpanda |
| AI / ML | Scikit-learn + XGBoost + River |
| Hot State | In-memory Python/River + Redis Data Structures |
| Pub/Sub | Redis Pub/Sub (live alert fan-out) |
| Persistent Storage | PostgreSQL |
| Real-time | WebSockets |
| Security | JWT + RBAC + Argon2 |
| Infrastructure | Docker + Docker Compose |
| Observability | Structured JSON Logging + Prometheus + Grafana |

---

## Environment Setup

Copy the environment template and fill in your values. **Never commit `.env`.**

```bash
cp .env.example .env
```

### Network Connectivity Notes

| Context | Redpanda Address |
|---|---|
| Inside Docker (FastAPI backend) | `redpanda:9092` |
| Host machine (PCAP / demo scripts) | `localhost:19092` |

---

## Running the Stack (Docker)

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend (React) | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/alerts` | List alerts with filters |
| `GET` | `/api/v1/alerts/{id}` | Get alert detail |
| `PATCH` | `/api/v1/alerts/{id}/status` | Update alert status |
| `GET` | `/api/v1/incidents` | List incidents |
| `GET` | `/api/v1/incidents/{id}` | Get incident detail |
| `POST` | `/api/v1/narrative/generate` | Generate AI narrative for an alert |
| `GET` | `/api/v1/dashboard/stats` | Dashboard summary statistics |
| `WS` | `/ws/alerts` | Live alert WebSocket stream |
| `GET` | `/health` | Health check |

---

## Running the Live Demo (PCAP)

To drive detections using a PCAP file while the Docker stack is running:

```bash
# 1. Set up a Python environment with requirements installed
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt

# 2. Run the live demo script (targets host-side Redpanda at localhost:19092)
python scripts/live_demo.py --pcap /path/to/traffic.pcap
```

The script replays the PCAP through the Ingest Normalizer → Redpanda pipeline, triggering the full detection flow in real time.

---

## Source-of-Truth Documents

| Document | Purpose |
|---|---|
| [`docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md`](docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md) | Locked architecture decisions |
| [`docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md`](docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md) | Canonical event contract |
| [`docs/shared/API_CONTRACT_DRAFT_v1.md`](docs/shared/API_CONTRACT_DRAFT_v1.md) | REST + WebSocket API contract |
| [`AGENTS.md`](AGENTS.md) | Agent governance and project rules |

---

## Contributing / Agent Rules

All AI agents working on this project must read [`AGENTS.md`](AGENTS.md) before making any changes. It governs:

- Architecture protection rules
- Documentation synchronisation requirements
- Git and branch workflow
- Approval / escalation rules
- Locked vs conditional vs open decisions
