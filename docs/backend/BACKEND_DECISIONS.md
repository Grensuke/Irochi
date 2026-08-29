# Backend Decisions — Irochi

> **This file records stable backend-area decisions.**
> It is NOT a chat history. Add entries when decisions are made.

---

## BD-001: Python + FastAPI

**Status:** Locked

Python + FastAPI is the backend application framework. FastAPI provides REST endpoints, WebSocket endpoints, authentication, authorization, and dashboard data access. FastAPI is **not** the primary high-volume packet-processing engine.

## BD-002: Redpanda as Streaming Transport

**Status:** Locked

Redpanda is the internal event-stream transport that decouples ingestion, feature processing, detection, and other backend stages. Exact topic names/topology are not yet finalized.

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

**Status:** Active

During the dummy/scaffold phase, no real Zeek parsing, Redpanda producers/consumers, Redis, PostgreSQL persistence, ML models, detectors, or production authentication are implemented. Clean interfaces and placeholders are created so these can be introduced later.

## BD-007: Abstract Service Layer Pattern

**Status:** Active

Backend services use abstract base classes (`AlertService`, `DashboardService`) with mock implementations (`MockAlertService`, `MockDashboardService`). Future real implementations (e.g. PostgreSQL-backed) must implement the same interface. This allows swapping mock → real without changing routes or schemas.

## BD-008: Threat Taxonomy Enum Values

**Status:** Active

Mock alert data uses consistent enum values for threat types and detector IDs, matching the taxonomy from the architecture checkpoint:

**Detector IDs (5):** `ddos_detector`, `recon_detector`, `dns_dga_tunnel_detector`, `tls_c2_detector`, `exfiltration_detector`

**Threat Types (6):** `volumetric_ddos`, `c2_beaconing`, `dga_dns_tunnel`, `encrypted_malware`, `recon_portscan`, `data_exfiltration`

**Severities:** `critical`, `high`, `medium`, `low`, `info`

These values are not yet formally locked in the final API contract but are used consistently across the dummy backend and should be carried forward unless the final contract changes them.

## BD-009: Raw Redpanda Topic Partition Key

**Status:** Locked

All raw canonical-event Redpanda topics use `src_ip` as the partition key:

- `irochi.events.connection.v1` → `hash(src_ip)`
- `irochi.events.dns.v1` → `hash(src_ip)`
- `irochi.events.tls.v1` → `hash(src_ip)`

This decision was approved after evaluating the Feature/Window aggregation requirements. Destination-centric DDoS aggregation and pair-centric C2 beaconing require downstream shared state rather than relying on raw-topic partition locality. The currently defined TLS features provide no identified benefit from TLS-topic `(src_ip, dst_ip)` locality.

This locks the partition key only. It does not lock raw-topic partition counts, retention values, downstream Feature/Window topics, or other remaining Redpanda design decisions.

