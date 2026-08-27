# Backend Context — Irochi

> **This file describes the CURRENT state of the backend.**
> It is NOT a conversation transcript. Update it after each approved checkpoint.

---

## Phase

Repository initialization / dummy backend

## Completed

- Repository and workflow structure setup (Checkpoint 1)
- Documentation structure created (Checkpoint 1)
- FastAPI skeleton with dummy endpoints (Checkpoint 2)
- Pydantic schemas for alerts, dashboard, and health (Checkpoint 2)
- Mock alert service with 12 static alerts covering all 6 threat types and all 5 detectors (Checkpoint 2)
- Mock dashboard summary service (Checkpoint 2)
- Dummy WebSocket endpoint with backfill + live simulation (Checkpoint 2)
- Service layer with abstract interfaces for future replacement (Checkpoint 2)
- Backend Dockerfile (Checkpoint 2)
- 20 passing tests (health, alerts, dashboard, WebSocket) (Checkpoint 2)

## Current Task

Frontend skeleton and dashboard (Checkpoint 3, pending approval)

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

## Pending

- Redpanda topic design
- Feature/Window Schema
- Detector input/output contracts
- Alert Schema
- PostgreSQL schema
- Real Zeek integration
- Real ML models
- Production Redis (hot state + Pub/Sub)
- Real NetFlow/IPFIX adapter
- Production authentication (JWT + RBAC + Argon2)
- Final API contract
- Final WebSocket protocol

## Known Constraints

- Real detection pipeline is not implemented
- Mock services are temporary placeholders
- Final API contract is not locked
- No real database, message broker, or ML in this phase
- CORS is permissive ("*") for dummy phase
- WebSocket live interval is 4 seconds (configurable in core/config.py)

## Next Steps

Build the frontend skeleton and dashboard (Checkpoint 3).
