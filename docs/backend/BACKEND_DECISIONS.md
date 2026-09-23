# Backend Decisions — Vibhinetra

> **This file records stable backend-area decisions.**
> It is NOT a chat history. Add entries when decisions are made.

---

## BD-001: Python + FastAPI

**Status:** Locked

Python + FastAPI is the backend application framework. FastAPI provides REST endpoints, WebSocket endpoints, authentication, authorization, and dashboard data access. FastAPI is **not** the primary high-volume packet-processing engine.

## BD-002: Redpanda as Streaming Transport

**Status:** Locked

Redpanda is the internal event-stream transport that decouples ingestion, feature processing, detection, and other backend stages.
Exact topic names/topology remain subject to the Redpanda design documents.
The raw-topic partition key is separately tracked in BD-009; other Redpanda
topology decisions remain open until explicitly approved.

## BD-003: PostgreSQL as Durable Alert Truth

**Status:** Locked

PostgreSQL is the persistent source of truth for alerts and other durable data. TimescaleDB is **conditional** — not to be added unless schema/retention/data-volume/query analysis justifies it.

## BD-004: Redis — Separate Hot State and Pub/Sub Roles

**Status:** Locked

Redis has two distinct roles:

1. **Redis Data Structures** → shared hot state (rolling counters, cross-worker state, hot dashboard metrics)
2. **Redis Pub/Sub** → live alert fan-out to FastAPI workers

These are separate concerns. Do not route every event through Redis.

## BD-005: PostgreSQL Commit Precedes Alert Pub/Sub

**Status:** Locked

An alert must be successfully committed to PostgreSQL before its ID/message is published to Redis Pub/Sub. This prevents a WebSocket client from receiving an alert notification before its durable record exists.

```
Alert Engine → PostgreSQL INSERT → AWAIT COMMIT → success? → Redis Pub/Sub
```

## BD-006: Real Pipeline Not Implemented During Initialization

**Status:** Obsolete

This decision governed the initial scaffolding phase. The real pipeline (Zeek ingest, Redpanda, Redis, PostgreSQL persistence, active ML detectors) is now implemented and active. Production authentication remains planned.

## BD-007: Abstract Service Layer Pattern

**Status:** Active

Backend services use abstract base classes (`AlertService`, `DashboardService`) with implementation-specific subclasses. This allowed swapping from initial mock implementations to the current real, active implementations (e.g. `PostgresAlertService`, `RedisPubSubService`) without changing routes or schemas.

## BD-008: Threat Taxonomy Enum Values

**Status:** Active

Mock alert data uses consistent enum values for threat types and detector IDs, matching the taxonomy from the architecture checkpoint:

**Detector IDs (6):** `ddos_detector`, `recon_detector`, `dns_dga_tunnel_detector`, `tls_c2_detector`, `exfiltration_detector`, `unknown_detector`

**Threat Types (7):** `volumetric_ddos`, `c2_beaconing`, `dga_dns_tunnel`, `encrypted_malware`, `recon_portscan`, `data_exfiltration`, `unknown_threat`

**Severities:** `critical`, `high`, `medium`, `low`, `info`

These values are not yet formally locked in the final API contract but are used consistently across the active backend and should be carried forward unless the final contract changes them.

## BD-009: Raw Redpanda Topic Partition Key

**Status:** Locked
**Approval provenance:** AR-01

All raw canonical-event Redpanda topics use `src_ip` as the partition key:

- `vibhinetra.events.connection.v1` → `hash(src_ip)`
- `vibhinetra.events.dns.v1` → `hash(src_ip)`
- `vibhinetra.events.tls.v1` → `hash(src_ip)`

This decision was approved after evaluating the Feature/Window aggregation requirements. Destination-centric DDoS aggregation and pair-centric C2 beaconing require downstream shared state rather than relying on raw-topic partition locality. The currently defined TLS features provide no identified benefit from TLS-topic `(src_ip, dst_ip)` locality.

See `docs/architecture/REDPANDA_TOPICS_DRAFT_v5.md` §4 and `docs/architecture/FEATURE_WINDOW_SCHEMA_DRAFT_v7.md` §7 for the full reasoning and supporting analysis.

This locks the partition key only. It does not lock raw-topic partition counts, retention values, downstream Feature/Window topics, or other remaining Redpanda design decisions.

## BD-010: Graceful ML Fallback

**Status:** Locked

All ML-based detector signals (such as XGBoost models or River streaming algorithms) must implement graceful fallback mechanisms. If a required model artifact is missing or an ML dependency fails to load (e.g. Cython build issues on specific operating systems), the detector must catch the exception, log a warning/error, and fall back to purely rule-based evaluation rather than crashing the pipeline.

## BD-011: Dynamic Severity Distribution vs Default Fallbacks

**Status:** Locked

Detectors must actively evaluate confidence, probability scores, and statistical deviations to compute a dynamic `severity_candidate` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) rather than relying on a hardcoded fallback (`None`). The `AlertEngine` relies on this distribution to paint an accurate and prioritized operational picture on the SOC dashboard. Hardcoded `MEDIUM` defaults are prohibited for functional detectors.
