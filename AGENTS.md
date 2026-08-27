# AGENTS.md — Irochi Project Root

## Project

**Irochi** — SIH 2026 Problem Statement **SIH26145**

Passive, real-time network threat-detection and security-intelligence system.

---

## Source-of-Truth Documents

| Document | Path | Purpose |
|---|---|---|
| Architecture Checkpoint | `docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md` | Project-level architectural truth — locked decisions, conditional decisions, component order, invariants |
| Canonical Event Schema | `docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md` | Data-contract truth — source-independent event structure produced by the Ingest Normalizer |

### Document Hierarchy

- **Architecture Checkpoint** → project-level truth; governs all architecture decisions.
- **Canonical Event Schema** → data-contract truth; governs all event/schema decisions.
- **Backend/Frontend Context files** → working memory; describe CURRENT project state for each area.
- **Backend/Frontend Decision files** → area-specific stable decisions.
- **Shared documents** (`docs/shared/`) → cross-team contracts and integration coordination.

---

## Rules for All Agents

1. **Read `AGENTS.md` first** before doing any work.
2. **Read the relevant context file** (`docs/backend/BACKEND_CONTEXT.md` or `docs/frontend/FRONTEND_CONTEXT.md`) before working on that area.
3. **Read the Architecture Checkpoint** before proposing or making any architecture change.
4. **Read the Canonical Event Schema** before making any event/schema change.
5. **Do not modify locked architecture** without explicit project-lead approval.
6. **Do not turn conditional decisions into locked decisions** — conditional items remain conditional until their stated decision point is reached.
7. **Do not use context files as chat transcripts** — they describe current project state, not conversation history.
8. **Context files describe CURRENT PROJECT STATE** — update them after each approved checkpoint to reflect what was actually completed.
9. **Decision files contain stable area-specific decisions** — add entries when a decision is made, do not remove past entries.
10. **Cross-team contracts belong in `docs/shared/`** — API contracts, data contracts, and integration requests go there.
11. **Do not directly connect React to PostgreSQL, Redis, or Redpanda** — the frontend communicates exclusively through FastAPI REST and WebSocket endpoints.
12. **Do not create unnecessary microservices** — the five detector modules are logical modules, not separate services.
13. **Keep raw vs derived data separate** — canonical events contain observed facts; derived/windowed features belong to the Feature/Window Schema.
14. **Never silently change the technology stack** — any stack change requires explicit project-lead approval.

---

## Technology Stack (Locked)

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

> **TimescaleDB** is conditional — do not add it unless schema/retention/volume/query analysis justifies it.

---

## Repository Layout

```
Irochi/
├── .agents/              # Antigravity skills (do not modify installed skills)
├── docs/
│   ├── architecture/     # Architecture checkpoint (source of truth)
│   ├── data/             # Canonical Event Schema (source of truth)
│   ├── backend/          # Backend context + decisions
│   ├── frontend/         # Frontend context + decisions
│   └── shared/           # Cross-team: API contract, data contracts, integration notes
├── frontend/             # React + Vite + TypeScript
├── backend/              # Python + FastAPI
├── infra/                # Infrastructure configs
├── tests/                # Cross-cutting tests
├── AGENTS.md             # This file
├── README.md             # Project README
├── .gitignore
├── .env.example
└── docker-compose.yml
```

This is a **monorepo**. Do not create separate Git repositories inside `frontend/` or `backend/`.
