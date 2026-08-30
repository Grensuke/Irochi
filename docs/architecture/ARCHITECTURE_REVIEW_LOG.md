# Architecture Review Log

## AR-01 — Review 1
- **Reviewer / Approver:** Project Lead
- **Date:** 2026-08-30
- **Status:** APPROVED
- **Scope:**
  - `docs/architecture/REDPANDA_TOPICS_DRAFT_v5.md`
  - `docs/architecture/FEATURE_WINDOW_SCHEMA_DRAFT_v7.md`
  - BD-009 in `docs/backend/BACKEND_DECISIONS.md`
  - Feature/Window Task 16a four-lock provenance review
- **Project-lead decision:** APPROVED
- **Decisions promoted/confirmed as LOCKED:**
  1. BD-009: All raw canonical-event Redpanda topics use `hash(src_ip)` as the partition key (`irochi.events.connection.v1`, `irochi.events.dns.v1`, `irochi.events.tls.v1`).
  2. Feature/Window Task 16a: Snapshot-not-delta processing invariant.
  3. Feature/Window Task 16a: DDoS atomic counter baseline using INCR/HINCRBY.
  4. Feature/Window Task 16a: Directional pair identity `(src_ip, dst_ip)`.
  5. Feature/Window Task 16a: Tier 1 / Tier 2 pair-state split and roles.
- **Decisions retained as PROPOSED:** Existing PROPOSED items unchanged.
- **Decisions retained as OPEN:** Existing OPEN items unchanged.
- **Notes:** Approval establishes formal AR-01 provenance; no additional decisions are promoted. This approval does not lock any parameters or implementation details that remain OPEN or PROPOSED (e.g., partition counts, retention, memory budgets, thresholds).

## [AR-02] Architecture Review 2

- **Review ID:** AR-02
- **Reviewer / Approver:** Project Lead
- **Date:** 2026-08-30
- **Status:** APPROVED
- **Scope:**
  - docs/architecture/DETECTOR_IO_CONTRACT_DRAFT_v1.md
  - docs/architecture/ALERT_SCHEMA_DRAFT_v1.md
- **Project-lead decision:** APPROVED
- **Decisions approved:**
  1. Enrichment records (`entity_type` and `entity_key`) are explicitly required; identity propagated through envelope.
  2. `event` entity_type is APPROVED FOR REMOVAL. Canonical `entity_type` is 4-value: `source`, `destination`, `pair`, `connection`.
- **Decisions retained PROPOSED:** Remaining Detector I/O and Alert Schema structural contracts.
- **Decisions retained OPEN:** Temporal deduplication, scores, staleness algorithm.
- **Notes:** AR-02 decision resolves the enrichment identity contradiction upstream and drops the downstream `event` workaround.

## [AR-03] Architecture Review 3

- **Review ID:** AR-03
- **Reviewer / Approver:** Project Lead
- **Date:** 2026-08-30
- **Status:** APPROVED
- **Scope:**
  - PostgreSQL Schema v1
  - API Contract Draft v1
- **Project-lead decision:** APPROVED
- **Decisions promoted/confirmed as LOCKED:**
  1. **PostgreSQL Core Persistence Model:** Canonical Alert → PostgreSQL logical field mapping, required/nullable semantics, core dedup component columns (`detector_id`, `threat_type`, `entity_type`, `entity_key`), and `evidence`/`alert_context` JSONB representation.
  2. **API Presentation Model:** Four MVP REST endpoint contract surfaces, AlertResponse structural schema, ISO 8601 timestamp presentation, confidence nullable behavior, four-value entity presentation, entity-derived IP/port rules, WebSocket `{type, alert}` envelope, and `backfill_complete` semantics with `alert: null`.
- **Decisions retained PROPOSED:** `update_count` baseline structural field, `dedup_digest`, UPDATE commit-before-publish extension.
- **Decisions retained OPEN:** Exact stale-update/concurrency algorithm, temporal deduplication scope, exact physical indexes, ORM implementation details, migration implementation details, PostgreSQL partitioning, PostgreSQL retention, exact dashboard metric definitions.
- **Notes:** AR-03 establishes the approved logical persistence target for subsequent ORM/migration implementation and locks the API presentation contract. AR-03 explicitly does NOT promote any implementation-dependent or measurement-dependent item to LOCKED.
