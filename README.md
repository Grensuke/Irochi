# Vibhinetra



**Problem Statement Title:** AI-Based Detection of Cyber Threats in Unidirectional IP Traffic

Vibhinetra is a passive, real-time network threat-detection and security-intelligence system for unidirectional IP traffic.

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
> - **NEW:** Dynamic severity distribution (LOW, MEDIUM, HIGH, CRITICAL) intelligently assigned across all detectors
> - **NEW:** Silent background refetching for real-time dashboard reactivity without visual loading flashes
>
> **Known limitations:**
> - ML detectors (DNS/DGA, Exfiltration) require external `.joblib` model artifacts to utilize their full capabilities (they gracefully fallback to rule-based/default detection if missing).
> - Window duration and threshold tuning is ongoing (see evaluation docs)
> - TimescaleDB is not yet enabled (conditional decision, not locked)

---

## What Vibhinetra Is (and Is Not)

Vibhinetra is a **passive intelligence system**. It strictly:

- Observes unidirectional IP traffic passively
- Normalises traffic from multiple sources (Zeek logs, NetFlow/IPFIX)
- Detects and classifies cyber threats with confidence scores
- Produces labelled security alerts with supporting evidence
- Clusters related alerts into incidents for analyst workflow
- Delivers alerts live to a React security dashboard via WebSockets

Vibhinetra does **NOT**:
- Probe or contact traffic sources/destinations
- Decrypt TLS/QUIC payloads
- Send mitigation or blocking commands
- Act inline on production network traffic

> **"Closed" is an analyst workflow status.** It does not mean Vibhinetra blocked or mitigated the threat.

---

## Threat Capabilities

| # | Threat Capability | Detector Module | Status |
|---|---|---|---|
| 1 | Volumetric / Protocol DDoS | DDoS Detector | **Active** (River ML signal) |
| 2 | Reconnaissance / Port Scanning | Recon Detector | **Active** |
| 3 | DGA / DNS Tunneling | DNS/DGA/Tunnel Detector | **Active** (requires Scikit `.joblib`) |
| 4 | Botnet C2 Beaconing | TLS/C2 Detector | **Active** (behavioral heuristic) |
| 5 | Malware inside encrypted sessions | TLS/C2 Detector | **Active** (behavioral heuristic) |
| 6 | Data Exfiltration | Exfiltration Detector | **Active** (requires XGBoost `.joblib`) |
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

See [`docs/architecture/_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md`](docs/architecture/_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md) for the full annotated architecture.

---

## Repository Structure

```
Vibhinetra/
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
| Security | Mock Auth Context (JWT + RBAC + Argon2 are Planned) |
| Infrastructure | Docker + Docker Compose |
| Observability | Structured JSON Logging (Prometheus + Grafana are Planned) |

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

## Deployment Setup

### 1. Local Development
Runs the full stack with Vite dev server and FastAPI with `--reload`. Includes the demo traffic generator.
```bash
docker compose up --build
```
| Service | URL |
|---|---|
| Frontend (React) | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

### 2. Demo Deployment
Runs the production multi-stage builds, but leaves the synthetic `traffic-generator` active to pump mock data.
```bash
docker compose -f docker-compose.prod.yml up --build -d
```
(Requires `DEMO_MODE=true` in `.env`)

### 3. Production Deployment (Real Traffic)
Runs the hardened production stack. No dummy traffic. Wait for real Zeek telemetry.
```bash
docker compose -f docker-compose.prod.yml up --build -d
```
**Important Production Requirements:**
- Must set `DEMO_MODE=false` in `.env`.
- Must provide strong `SECRET_KEY` and `POSTGRES_PASSWORD` in `.env` (the backend will refuse to start on default values in production).
- Must configure `CORS_ALLOWED_ORIGINS` (e.g. `https://yourdomain.com`).
- ML Models: Both `dns_dga_model_v1.joblib` and `exfil_model_v1.joblib` (with their respective `.meta.json` files) **must** be present in the `models/` directory. The production backend will explicitly fail to start if they are missing. (In development, it gracefully falls back to rule-based detection).
- Infrastructure ports (PostgreSQL, Redis, Redpanda) are **not** exposed to the host network.
- The React frontend is served via an Nginx reverse proxy on port 80 (configured via `FRONTEND_PORT`).

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

## How the Live Demo Works

The live demo is now **completely automated** via the `traffic-generator` container in Docker Compose. You do not need to run any manual scripts to drive traffic into the pipeline.

**The Pipeline Flow:**
1. **Traffic Generator:** The `vibhinetra-traffic-generator` container continuously loops through the pre-processed `real_demo_traffic.jsonl` tape and pumps the network events into the Redpanda broker.
2. **Detection & Correlation:** The backend consumes from Redpanda, runs the features through 6 ML/heuristic detectors, and persists Alerts to PostgreSQL. The Incident Engine then clusters them.
3. **Real-Time UI Delivery:** The backend publishes the new Alerts to a Redis Pub/Sub channel. The FastAPI WebSocket service picks these up and pushes them to the React frontend in real-time.

To reset the demo database manually if desired, you can still run the script from the host environment:
```bash
cd backend
.venv\Scripts\python.exe scripts\playback_demo.py --clear
```

---

## Source-of-Truth Documents

| Document | Purpose |
|---|---|
| [`docs/architecture/_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md`](docs/architecture/_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md) | Locked architecture decisions |
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
