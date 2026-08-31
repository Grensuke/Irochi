# Backend Context — Irochi

> **This file describes the CURRENT state of the backend.**
> It is NOT a conversation transcript. Update it after each approved checkpoint.

---

## Phase

WP-C (Redpanda + Redis Streaming Foundation) Completed. Preparing for WP-D.

## Implementation Status

**Architecture Decisions:**
- AR-01 ✅ APPROVED
- AR-02 ✅ APPROVED
- AR-03 ✅ APPROVED

**Work Packages:**
- WP-A ✅ MERGED
- WP-B ✅ MERGED
- WP-C ✅ MERGED
- WP-D = CURRENT / NEXT
- WP-E = PENDING
- WP-F = PENDING — all five logical detectors
- WP-G = PENDING
- WP-H = PENDING
- WP-I = PENDING
- M8 = PENDING — end-to-end MVP validation

**Milestones:**
- P0 = first complete vertical slice with one functional detector
- P1 = full SIH MVP with all five logical detectors
- P2 = production-oriented hardening

**Important Constraints:**
- The exact stale-update/concurrency algorithm is OPEN.
- It must be resolved before Alert Engine persistence.

## Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point, CORS, route mounting
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py     # GET /api/v1/health
│   │   │   ├── alerts.py     # GET /api/v1/alerts, /alerts/{id}
│   │   │   └── dashboard.py  # GET /api/v1/dashboard/summary
│   │   └── websocket/
│   │       └── alerts.py     # WS /api/v1/ws/alerts
│   ├── schemas/
│   │   ├── health.py         # HealthResponse
│   │   ├── alerts.py         # AlertResponse, enums, WebSocketMessage
│   │   └── dashboard.py      # DashboardSummaryResponse
│   ├── services/
│   │   ├── alert_service.py  # AlertService interface + MockAlertService
│   │   └── dashboard_service.py  # DashboardService interface + MockDashboardService
│   ├── core/
│   │   └── config.py         # App metadata, API prefix, WS settings
│   └── mock/
│       └── data.py           # 12 static mock alerts + 6 live templates
├── tests/
│   ├── conftest.py           # TestClient fixture
│   ├── test_health.py        # 2 tests
│   ├── test_alerts.py        # 9 tests
│   ├── test_dashboard.py     # 6 tests
│   └── test_websocket.py     # 3 tests
├── Dockerfile
├── requirements.txt
└── README.md
```

## Endpoints

| Method | Path | Status |
|---|---|---|
| GET | `/api/v1/health` | ✅ Working |
| GET | `/api/v1/alerts` | ✅ Working |
| GET | `/api/v1/alerts/{alert_id}` | ✅ Working (404 for missing) |
| GET | `/api/v1/dashboard/summary` | ✅ Working |
| WS | `/api/v1/ws/alerts` | ✅ Working (backfill + live) |

## Design Contracts (current status per DATA_CONTRACTS.md)

- Redpanda topic design — DRAFT / IN PROGRESS
- Feature/Window Schema — DRAFT / IN PROGRESS
- Detector input/output contracts — DRAFT / IN PROGRESS
- Alert Schema — DRAFT / IN PROGRESS
- PostgreSQL Schema — DRAFT / IN PROGRESS
- Final API Contract — DRAFT / IN PROGRESS

## Pending

- Real Zeek integration
- Real ML models
- Production Redis (hot state + Pub/Sub)
- Real NetFlow/IPFIX adapter
- Production authentication (JWT + RBAC + Argon2)
- Final API contract implementation (contract design is DRAFT / IN PROGRESS in `docs/shared/API_CONTRACT_DRAFT_v1.md`; runtime implementation is pending)
- Final WebSocket protocol implementation (contract design is DRAFT / IN PROGRESS; runtime implementation is pending)

## Known Constraints

- Real detection pipeline is not implemented
- Mock services are temporary placeholders
- Final API contract is not locked
- No real database, message broker, or ML in this phase
- CORS is permissive ("*") for dummy phase
- WebSocket live interval is 4 seconds (configurable in core/config.py)

## Next Steps

Wait for project lead approval to proceed to production infrastructure (Checkpoint 5).
