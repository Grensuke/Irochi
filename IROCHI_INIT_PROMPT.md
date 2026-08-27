You are initializing the Irochi repository for SIH 2026 Problem Statement SIH26145.

This is the INITIAL REPOSITORY + WORKFLOW SETUP + THIN DUMMY VERSION.

Do NOT implement the real cybersecurity detection pipeline yet.

==================================================
0. FIRST ACTION — READ THE SOURCE-OF-TRUTH FILES
==================================================

Before creating or modifying anything, read these exact files:

docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md

docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md

These are the current architecture/data reference documents.

IMPORTANT:
- Do not rename them.
- Do not rewrite them.
- Do not "improve" locked architecture decisions.
- Do not invent replacements for decisions already made.
- Do not silently finalize anything marked conditional/open.
- If something is not defined, create a clean placeholder/interface and leave the design open.
- The architecture checkpoint is the highest-level project reference.
- The Canonical Event Schema is the reference for canonical event structure.

Project:
Irochi

SIH Problem Statement:
SIH26145

==================================================
1. EXECUTION MODE — WORK IN CHECKPOINTS
==================================================

Do NOT perform the entire task in one uncontrolled pass.

Work in these checkpoints:

CHECKPOINT 1:
Repository workflow files and documentation structure.

Then STOP and show:
- files created
- files modified
- resulting structure
- any ambiguity

Wait for approval.

CHECKPOINT 2:
Backend skeleton + dummy API.

Then STOP and show:
- backend structure
- endpoints
- tests
- any issues

Wait for approval.

CHECKPOINT 3:
Frontend skeleton + dashboard.

Then STOP and show:
- frontend structure
- pages/components
- design decisions
- build/type-check result

Wait for approval.

CHECKPOINT 4:
Dummy backend/frontend integration + dummy WebSocket behavior + final validation.

Then STOP.

Do not proceed from one checkpoint to the next without explicit approval.

==================================================
2. LOCKED TECHNOLOGY STACK
==================================================

Frontend:
- React
- Vite
- TypeScript

Backend:
- Python
- FastAPI

Network telemetry:
- Zeek
- Python Ingest Normalizer

Streaming:
- Redpanda

AI/ML:
- Scikit-learn
- XGBoost
- River

Hot state:
- In-memory Python/River state
- Redis

Persistent storage:
- PostgreSQL
- TimescaleDB remains conditional and must NOT be added now

Realtime:
- WebSockets

Security:
- JWT
- RBAC
- Argon2

Infrastructure:
- Docker
- Docker Compose

Observability:
- Structured JSON logging
- Prometheus
- Grafana

Frontend design:
- Use the installed UI UX Pro Max skill.
- Use the installed Taste frontend/design skill.
- Do not replace React + Vite + TypeScript.

==================================================
3. CORE ARCHITECTURE RULES
==================================================

Respect all locked rules from the architecture checkpoint.

Especially:

- PostgreSQL is the durable source of truth.
- Redis has two separate roles:
  1. hot/shared state
  2. Pub/Sub live alert fan-out
- Alert publication ordering is:

    Alert Engine
      ↓
    PostgreSQL INSERT
      ↓
    await COMMIT
      ↓
    success?
      ├── NO  → log/retry, do not publish
      └── YES → Redis Pub/Sub

- React never connects directly to PostgreSQL, Redis, or Redpanda.
- WebSocket reconnect recovery uses PostgreSQL backfill before relying on the live stream.
- Do not make every detector a microservice.
- NetFlow/IPFIX does not go through Zeek.
- Raw canonical fields must remain separate from derived/windowed features.
- Do not finalize currently conditional/open architecture decisions.
- Do not claim benchmark performance before measurement.

==================================================
4. REPOSITORY STRUCTURE
==================================================

Create this structure:

Irochi/
├── .agents/
│   └── skills/
│       └── existing installed skills must remain untouched
│
├── docs/
│   ├── architecture/
│   │   └── SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md
│   │
│   ├── data/
│   │   └── CANONICAL_EVENT_SCHEMA_FINAL.md
│   │
│   ├── backend/
│   │   ├── BACKEND_CONTEXT.md
│   │   └── BACKEND_DECISIONS.md
│   │
│   ├── frontend/
│   │   ├── FRONTEND_CONTEXT.md
│   │   └── FRONTEND_DECISIONS.md
│   │
│   └── shared/
│       ├── API_CONTRACT.md
│       ├── DATA_CONTRACTS.md
│       └── INTEGRATION_NOTES.md
│
├── frontend/
├── backend/
├── infra/
├── tests/
├── AGENTS.md
├── README.md
├── .gitignore
├── .env.example
└── docker-compose.yml

Do not create separate Git repositories inside frontend/ or backend/.

This is a monorepo.

==================================================
5. AGENTS.md
==================================================

Create a root AGENTS.md for all future agents.

It must explain:

- Project name: Irochi
- Problem statement: SIH26145
- Exact source-of-truth file paths:
  docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md
  docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md

Rules for future agents:

1. Read AGENTS.md first.
2. Read the relevant context file before working.
3. Read the architecture checkpoint before architecture changes.
4. Read the canonical event schema before event/schema changes.
5. Do not modify locked architecture without explicit project-lead approval.
6. Do not turn conditional decisions into locked decisions.
7. Do not use context files as chat transcripts.
8. Context files describe CURRENT PROJECT STATE.
9. Decision files contain stable area-specific decisions.
10. Cross-team contracts belong in docs/shared/.
11. Do not directly connect React to PostgreSQL, Redis, or Redpanda.
12. Do not create unnecessary microservices.
13. Keep raw vs derived data separate.
14. Never silently change the technology stack.

Explicitly state:
- the architecture checkpoint is project-level truth;
- the Canonical Event Schema is data-contract truth;
- backend/frontend context files are working memory;
- backend/frontend decision files are area-specific stable decisions.

==================================================
6. BACKEND_CONTEXT.md
==================================================

Create:

docs/backend/BACKEND_CONTEXT.md

Initial content must reflect the actual state at Checkpoint 1.

Use this:

Phase:
Repository initialization / dummy backend

Completed:
- repository/workflow setup

Current task:
Dummy backend foundation

Pending:
- FastAPI skeleton
- dummy API
- backend tests
- Redpanda topic design
- Feature/Window Schema
- detector contracts
- Alert Schema
- PostgreSQL schema
- real Zeek integration
- real ML
- production Redis
- real NetFlow/IPFIX adapter

Known constraints:
- real detection pipeline is not implemented
- mock services are temporary
- final API contract is not locked

Next steps:
State the next backend task accurately.

After later checkpoints, update this file with the ACTUAL current state.

Do not write a conversation transcript.

==================================================
7. FRONTEND_CONTEXT.md
==================================================

Create:

docs/frontend/FRONTEND_CONTEXT.md

Initial content must reflect the actual state at Checkpoint 1.

Use:

Phase:
Repository initialization / dummy dashboard

Completed:
- repository/workflow setup

Current task:
Build the initial frontend foundation

Pending:
- React + Vite + TypeScript skeleton
- mock data layer
- dashboard shell
- dummy API integration
- final API contract
- final WebSocket contract
- real backend integration
- authentication
- real detection data

After later checkpoints, update this file with the ACTUAL current state.

Do not write a conversation transcript.

==================================================
8. AREA DECISIONS
==================================================

Create:

docs/backend/BACKEND_DECISIONS.md
docs/frontend/FRONTEND_DECISIONS.md

These are NOT chat history files.

Backend initial decisions:
- Python + FastAPI
- Redpanda is the future streaming transport
- PostgreSQL is durable alert truth
- Redis hot state and Redis Pub/Sub have separate roles
- PostgreSQL commit precedes alert Pub/Sub
- real pipeline is not implemented during initialization

Frontend initial decisions:
- React + Vite + TypeScript
- FastAPI is the backend boundary
- REST + WebSocket are intended integration mechanisms
- browser never accesses infrastructure services directly
- frontend initially uses mock services/data

Do not duplicate the entire architecture checkpoint.

==================================================
9. SHARED DOCUMENTS
==================================================

Create:

docs/shared/API_CONTRACT.md
docs/shared/DATA_CONTRACTS.md
docs/shared/INTEGRATION_NOTES.md

API_CONTRACT.md:
Clearly label it:

DRAFT / TEMPORARY DUMMY CONTRACT

Temporary endpoints:

GET /api/v1/health
GET /api/v1/alerts
GET /api/v1/alerts/{alert_id}
GET /api/v1/dashboard/summary
WS /api/v1/ws/alerts

State explicitly:
"These endpoints are temporary dummy endpoints. They are NOT the final API contract."

DATA_CONTRACTS.md:
Reference:

docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md

Do not create a contradictory duplicate schema.

INTEGRATION_NOTES.md:
Use for active frontend/backend integration requests.

Example format:

INT-001
Title:
From:
To:
Status:
Requirement:
Notes:

This file is for current integration work, not permanent architecture history.

==================================================
10. BACKEND DUMMY VERSION
==================================================

Create a clean FastAPI project.

Suggested structure:

backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── routes/
│   │   └── websocket/
│   ├── schemas/
│   ├── services/
│   ├── core/
│   └── mock/
├── tests/
├── requirements.txt
└── README.md

Requirements:

- app starts
- health endpoint works
- API uses /api/v1
- use Pydantic models
- routes/services/schemas are separated
- mock alert service
- mock dashboard summary service
- alert-by-id endpoint
- dummy WebSocket endpoint

Dummy endpoints:

GET /api/v1/health

Expected:
HTTP 200

Example:
{
  "status": "ok"
}

GET /api/v1/alerts

Return realistic mock alerts.

GET /api/v1/alerts/{alert_id}

Return one mock alert or a clear 404.

GET /api/v1/dashboard/summary

Return mock summary metrics.

WS /api/v1/ws/alerts

DUMMY BEHAVIOR:

1. Client connects.
2. Simulate a PostgreSQL-backed backfill by sending a small batch of existing mock alerts first.
3. After the simulated backfill, enter live mode.
4. Send a new mock alert periodically.
5. Keep the behavior deterministic enough for frontend development.
6. Make the distinction between "backfill" and "live" explicit in the message structure if practical.
7. This is only a simulation. Do NOT pretend PostgreSQL or Redis Pub/Sub is already implemented.

Do NOT implement:
- real Zeek parsing
- tcpreplay
- Redpanda producers/consumers
- real Redis
- PostgreSQL persistence
- real ML models
- real detectors
- production authentication
- final WebSocket protocol

Create clean interfaces/placeholders so these can be introduced later.

==================================================
11. FRONTEND DUMMY VERSION
==================================================

Create:

frontend/

using:

React + Vite + TypeScript

Use:
- UI UX Pro Max
- Taste frontend/design skill

Design direction:

Build a premium modern SOC/cybersecurity analyst dashboard.

Visual goals:
- dark security-operations interface
- high information density without clutter
- strong severity hierarchy
- high-contrast severity treatment
- monospace styling for IPs, hashes, alert IDs and technical values
- refined spacing and typography
- subtle borders/depth
- avoid generic admin-dashboard card overload
- avoid default-looking gray dashboard templates
- professional analyst workflow
- desktop-first
- responsive where appropriate

The UI should feel closer to a serious SOC/security operations product than a generic SaaS admin panel.

Minimum functionality:

- overview/summary section
- total alerts
- critical/high alert indicators
- recent alerts
- live alert feed
- threat category summary
- confidence indicators
- alert details
- loading state
- empty state
- error state
- connection state for the dummy WebSocket
- visible distinction between backfilled alerts and newly arriving live alerts

Use a frontend service layer:

frontend/src/services/

so mock services can later be replaced with real FastAPI calls.

Create types under:

frontend/src/types/

Do not couple UI components directly to mock data structures.

==================================================
12. IMPORTANT THREAT TAXONOMY
==================================================

There are FIVE logical detector modules:

1. DDoS Detector
2. Recon Detector
3. DNS/DGA/DNS-Tunneling Detector
4. TLS/C2 Detector
5. Exfiltration Detector

There are SIX threat capabilities shown to users:

1. Volumetric / Protocol DDoS
2. Botnet C2 Beaconing
3. DGA / DNS Tunneling
4. Malware inside encrypted sessions
5. Reconnaissance / Port Scanning
6. Data Exfiltration

These are NOT six microservices.

One logical detector module may emit multiple threat classes.

Mock alert data must include both:
- detector_id = one of the five canonical detector modules
- threat_type = one of the six threat capability classes

Keep these concepts separate so frontend/backend do not invent incompatible taxonomies.

==================================================
13. MOCK ALERT DATA
==================================================

Create realistic mock alerts covering all six threat capabilities.

Each mock alert should contain enough information for dashboard presentation, such as:

- alert_id
- timestamp
- threat_type
- detector_id
- severity
- confidence
- source/destination information where appropriate
- short evidence summary
- status

Do not confuse presentation alert fields with Canonical Event fields.

Do not add derived fields into the Canonical Event Schema merely because mock alerts display them.

==================================================
14. DOCKER / ENVIRONMENT
==================================================

Create a minimal docker-compose.yml appropriate for the dummy phase.

Do NOT bring up the entire production stack unless necessary.

Include .env.example.

Do not commit secrets.

Pin/document the runtime versions used by the project.

Do not silently introduce alternative databases, message brokers, frontend frameworks, or backend frameworks.

Create .gitignore as part of Checkpoint 1, BEFORE any backend or frontend dependencies are installed. At minimum it must exclude:
- Python: __pycache__/, *.pyc, .venv/, venv/, env/
- Node: node_modules/, dist/, build/
- Environment/secrets: .env (but NOT .env.example)
- OS/editor cruft: .DS_Store, .vscode/ (if not intentionally shared)

This must be in place and correct BEFORE Checkpoint 2's first local commit, so the backend virtual environment is never committed. Re-verify it again BEFORE Checkpoint 3's first local commit, so node_modules is never committed either.

==================================================
15. README.md
==================================================

Create a clear project README.

Include:

- Irochi
- SIH26145
- project purpose
- current status
- high-level architecture
- repository structure
- frontend setup/run instructions
- backend setup/run instructions
- dummy vs real implementation
- references to the architecture checkpoint
- reference to the Canonical Event Schema

Clearly label:

CURRENT:
Dummy/scaffold implementation

FUTURE:
Real streaming/ML/security pipeline

==================================================
16. TESTING
==================================================

Backend tests must verify:

- /api/v1/health returns 200 and {"status":"ok"}
- alerts endpoint returns expected structure
- alert-by-id works
- missing alert returns 404
- dashboard summary works
- dummy WebSocket can connect and emit mock data

Frontend checks:

- TypeScript checks
- production build succeeds
- basic application renders

Keep tests focused.

==================================================
17. DO NOT IMPLEMENT REAL ARCHITECTURE YET
==================================================

The following remain future work:

- real Redpanda topics
- real feature/window processing
- real detectors
- real ML models
- real Zeek ingestion
- real NetFlow/IPFIX adapter
- final PostgreSQL schema
- TimescaleDB evaluation
- final authentication
- final API contract
- final WebSocket contract
- production Redis state
- final alert schema

Do not invent these now.

==================================================
18. DOCUMENTATION UPDATE RULE
==================================================

At the end of each APPROVED checkpoint:

Update the relevant current-state file.

Backend work:
docs/backend/BACKEND_CONTEXT.md

Frontend work:
docs/frontend/FRONTEND_CONTEXT.md

Stable backend decision:
docs/backend/BACKEND_DECISIONS.md

Stable frontend decision:
docs/frontend/FRONTEND_DECISIONS.md

Cross-team integration:
docs/shared/INTEGRATION_NOTES.md

Do NOT modify the architecture checkpoint just to record ordinary implementation progress.

==================================================
19. GIT RULE
==================================================

Do NOT create a GitHub repository.

Do NOT push anywhere.

Do NOT create a remote.

You MAY create a LOCAL Git repository/commit ONLY after an entire checkpoint has been explicitly approved.

Before the FIRST local commit (i.e. after Checkpoint 1 is approved), confirm .gitignore is in place and correct per Section 14. Do not commit a virtual environment, node_modules, or .env.

After approval:

- create a local commit as a rollback checkpoint;
- do not push it;
- do not create or configure a remote.

This gives the project a local rollback point after each approved checkpoint while keeping repository ownership and GitHub setup under manual control.

==================================================
20. FINAL VALIDATION
==================================================

After CHECKPOINT 4:

1. Inspect repository structure.
2. Verify reference documents are still present and not corrupted.
3. Verify frontend build/type-check.
4. Verify backend tests.
5. Verify dummy WebSocket.
6. Verify frontend can consume dummy backend data.
7. Verify no real production infrastructure was accidentally implemented.
8. Verify no technology substitutions were made.
9. Verify the two source-of-truth documents were not rewritten.
10. Verify current-state context files accurately describe what was actually completed.
11. Verify no committed local Git history contains node_modules, a virtual environment, or .env.
12. Update README with actual commands.
13. Do NOT create/push a GitHub repository.
14. Do NOT move on to Redpanda Topic design.
15. Do NOT implement the real detection pipeline.
16. Stop and provide a concise final report.

Final report must contain:
- files created
- files modified
- backend run command
- frontend run command
- checks/tests performed
- intentional placeholders
- anything needing human approval

CRITICAL FINAL RULE:

This task is ONLY to establish:
- the Irochi repository structure,
- the Antigravity workflow/memory structure,
- and a clean dummy full-stack version.

Do not proceed to Redpanda Topic design.
Do not implement the real threat-detection pipeline.
Do not change locked architecture.
Do not finalize conditional architecture decisions.

==================================================
END OF INITIALIZATION INSTRUCTIONS
==================================================
