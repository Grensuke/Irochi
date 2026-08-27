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
