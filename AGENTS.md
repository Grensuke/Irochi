# AGENTS.md — Irochi Project Root

## Project
**Irochi**
**Problem Statement:** SIH26145
**Problem Statement Title:** AI-Based Detection of Cyber Threats in Unidirectional IP Traffic

Irochi is a passive/read-only cyber-threat detection and security-intelligence system for unidirectional IP traffic.

The system:
- observes passively collected traffic;
- detects and classifies threats;
- produces confidence scores and supporting evidence;
- provides security intelligence through alerts and dashboards.

The system does NOT:
- probe traffic sources;
- re-contact traffic sources/destinations;
- decrypt TLS/QUIC payloads;
- send mitigation commands;
- block traffic inline.

---

## Source-of-Truth Hierarchy

1. **AGENTS.md**
   → AI operating rules and repository workflow rules.

2. **Architecture Checkpoint** (`docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md`)
   → project-level architectural truth.
   → locked decisions, conditional decisions, invariants, component order.

3. **Canonical Event Schema** (`docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md`)
   → canonical source-independent data-contract truth.

4. **Shared Contracts** (`docs/shared/`)
   → cross-team API/data/integration contracts.

5. **Backend / Frontend Decision Files**
   → stable area-specific decisions.

6. **Backend / Frontend Context Files**
   → current working state.

7. **Source Code**
   → implementation of the above.

A lower-level implementation or document must NOT silently contradict a higher-level locked decision.

When a contradiction is discovered:
- do not silently choose an alternative;
- report the conflict;
- request project-lead approval where required.

---

## Rules for All AI Agents

All future agents must:

1. Read AGENTS.md first.
2. Identify which area they are working in.
3. Read the relevant context file before changing code.
4. Read relevant decision files before changing established behavior.
5. Read the Architecture Checkpoint before architecture changes.
6. Read the Canonical Event Schema before event/schema changes.
7. Read relevant shared contracts before frontend/backend integration work.
8. Inspect the current repository state before making assumptions.
9. Never silently change locked architecture or technology.
10. Never silently finalize a conditional/open decision.
11. Never claim a task is complete when known documentation or tests are inconsistent with the implementation.

---

## Locked Technology Stack

Preserve these technologies unless the project lead explicitly approves a change:

**Frontend:**
- React
- Vite
- TypeScript

**Backend:**
- Python
- FastAPI

**Network telemetry:**
- Zeek
- Python Ingest Normalizer

**Streaming:**
- Redpanda

**AI/ML:**
- Scikit-learn
- XGBoost
- River

**Hot state:**
- In-memory Python/River state
- Redis

**Persistent storage:**
- PostgreSQL

**Realtime:**
- WebSockets

**Security:**
- JWT
- RBAC
- Argon2

**Infrastructure:**
- Docker
- Docker Compose

**Observability:**
- Structured JSON logging
- Prometheus
- Grafana

*TimescaleDB remains conditional and must not be added merely because it is convenient.*

---

## Architecture Protection

Agents must preserve the approved architecture.

Especially:
- PostgreSQL is the durable alert source of truth.
- Redis hot state and Redis Pub/Sub are separate roles.
- Alert persistence ordering is:
    ```
    Alert Engine
        ↓
    PostgreSQL INSERT
        ↓
    await COMMIT
        ↓
    success?
       ├── NO  → log/retry, do not publish
       └── YES → Redis Pub/Sub
    ```
- React never connects directly to PostgreSQL.
- React never connects directly to Redis.
- React never connects directly to Redpanda.
- Frontend/backend communication occurs through approved APIs/WebSockets.
- Do not create unnecessary microservices.
- Five detector modules are logical modules, not five services.
- NetFlow/IPFIX does not go through Zeek.
- Raw canonical data and derived/windowed features remain separate.
- Irochi remains passive/read-only.

If implementation pressure conflicts with these rules, stop and report it instead of weakening the architecture silently.

---

## Documentation Synchronization

After meaningful work, the agent must determine whether the change affects:
- architecture;
- canonical data schema;
- shared data contract;
- API contract;
- WebSocket contract;
- backend decisions;
- frontend decisions;
- backend current state;
- frontend current state;
- cross-team integration.

Update the appropriate document when genuinely affected. Documentation and implementation must remain consistent.

Before declaring a task complete:
1. Check documentation impact.
2. Update affected documentation.
3. Check for contradictions.
4. Run relevant tests/checks.
5. Report documentation changes.

Do NOT modify unrelated documentation simply to create activity.

---

## Context File Rules

`*_CONTEXT.md` files describe CURRENT PROJECT STATE.

They should contain information such as:
- current phase;
- completed work;
- current task;
- pending work;
- blockers;
- next steps;
- important current constraints.

They are NOT:
- chat transcripts;
- discussion logs;
- copies of prompts;
- historical diaries.

Only record work that actually happened. Keep the context concise and useful for the next AI session.

---

## Decision File Rules

`*_DECISIONS.md` files contain stable, intentional, area-specific decisions.

A decision entry should normally include:
- decision;
- reason;
- status.

Do not record:
- guesses;
- unresolved questions;
- temporary implementation details;
- routine coding choices.

Do not silently delete a valid historical decision.

If a new approved decision replaces an old decision:
- retain the historical entry;
- clearly mark the old decision as superseded;
- record the new decision.

Project-level decisions belong in the Architecture Checkpoint, not only in a team-specific decision file.

---

## Shared Contract Rules

Shared contracts are the integration boundary between frontend and backend.

Relevant files include:
- `docs/shared/API_CONTRACT.md`
- `docs/shared/DATA_CONTRACTS.md`
- `docs/shared/INTEGRATION_NOTES.md`

Do not silently invent:
- new API endpoints;
- new API fields;
- new WebSocket message types;
- canonical event fields;
- backend capabilities.

If an interface change is required:
1. Identify whether the change is already covered by the contract.
2. Update the appropriate shared contract if it is an approved change.
3. Record cross-team implementation requirements appropriately.
4. Do not silently modify another team's implementation.

Do not use shared Markdown files as conversation transcripts.

---

## Backend Rules

Backend agents must:
- use Python + FastAPI;
- preserve the approved architecture;
- keep API/routes/services/schema responsibilities appropriately separated;
- preserve raw-vs-derived boundaries;
- respect Canonical Event Schema;
- never expose infrastructure directly to the browser;
- avoid unnecessary microservices;
- keep real infrastructure separate from dummy/mock implementations.

When a backend change affects frontend behavior:
- inspect the shared API/data contracts;
- update the relevant contract when appropriate;
- record integration requirements;
- do not assume frontend developers will infer undocumented behavior.

---

## Frontend Rules

Frontend agents must:
- use React + Vite + TypeScript;
- preserve the established Irochi product shell/design system;
- use the shared API/data contracts;
- not invent backend capabilities;
- use mock services for unfinished backend functionality;
- keep frontend presentation/domain types distinct from the Canonical Event Schema;
- not directly connect to PostgreSQL, Redis, or Redpanda.

When backend functionality does not yet exist:
- use centralized mock data/services;
- do not fake a production integration;
- document genuine integration requirements.

---

## Parallel Team Development

Frontend and backend may be developed simultaneously. Each team should primarily modify its own area.

Typical ownership:
- **Frontend:** `frontend/`, `docs/frontend/`
- **Backend:** `backend/`, `docs/backend/`
- **Shared:** `docs/shared/`, architecture/data contracts when explicitly approved

Rules:
- do not overwrite unrelated teammate changes;
- do not revert another team's work without approval;
- do not modify another team's code merely for convenience;
- use shared contracts as the coordination boundary;
- use the agreed GitHub Issues/PR workflow for active cross-team work once GitHub collaboration is established.

If a cross-team requirement is discovered:
- document it;
- do not silently implement the other team's portion.

---

## Git Rules

Git is a shared project-history mechanism.

Agents must:
- never create a GitHub remote without explicit project-lead approval;
- never push without explicit project-lead approval;
- never rewrite shared history;
- never force-push unless explicitly approved;
- verify `git status` before committing;
- keep commits small and meaningful;
- never commit secrets;
- never commit `.env`;
- never commit `node_modules/`;
- never commit `.venv/`, `venv/`, or other local environments;
- never commit caches or build artifacts;
- respect the repository `.gitignore`.

Do not use destructive Git commands against another teammate's work.

---

## Approval / Escalation Rules

Agents must stop and request project-lead approval when:
- a locked architecture decision must change;
- a locked technology must change;
- a conditional decision would need to become locked;
- a new API/data contract is needed but not defined;
- another team's implementation must be changed;
- requirements conflict with the source-of-truth documents;
- a change would materially alter project-level architecture;
- the agent cannot safely determine which design decision is intended.

Never resolve an architectural conflict by silently picking a new design.

---

## Test and Completion Rules

Before reporting meaningful work as complete:
1. Run relevant tests/checks.
2. Verify only intended files changed.
3. Check source-of-truth documents.
4. Check relevant context files.
5. Check relevant decision files.
6. Check shared contracts if interfaces changed.
7. Update documentation that genuinely changed.
8. Verify code and documentation agree.
9. Report issues, ambiguities, deviations, and unresolved items.

Never report "complete" while knowingly leaving a documentation or contract mismatch.

---

## Current Project Phase

Checkpoints 1–4 are complete.

Current state:
- repository/workflow foundation complete;
- dummy FastAPI backend complete;
- complete frontend product shell complete;
- dummy frontend ↔ backend integration complete;
- source-of-truth architecture/data documents preserved.

The next major work phase is real system design/implementation.

Do not assume the real production pipeline is already implemented. The current dummy system is a development baseline only.

---

## Important Threat Modeling Rule

The problem statement contains SIX user-facing threat capabilities:
1. Volumetric / Protocol DDoS
2. Botnet C2 Beaconing
3. DGA / DNS Tunneling
4. Malware inside encrypted sessions
5. Reconnaissance / Port Scanning
6. Data Exfiltration

The architecture contains FIVE logical detector modules:
1. DDoS Detector
2. Recon Detector
3. DNS/DGA/DNS-Tunneling Detector
4. TLS/C2 Detector
5. Exfiltration Detector

Do not turn the six threat capabilities into six microservices. One detector may produce multiple threat classes.

---

## Passive / Read-Only Product Semantics

Irochi is an intelligence/detection system.

"Closed" is an analyst workflow status.

"Closed" must never imply:
- attack mitigation;
- traffic blocking;
- automatic remediation.

Avoid terminology that implies Irochi can act back on the production network.

---

## Task-Specific Safety

When starting a task, determine:
- What part of the system am I changing?
- Which source-of-truth files govern it?
- Does this affect a shared contract?
- Does this affect another team's work?
- Does this require a new decision?
- Does this require project-lead approval?

Do not make broad repository changes when the task is narrowly scoped.
