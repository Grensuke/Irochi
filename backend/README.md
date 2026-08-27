# Irochi — Backend

**SIH 2026 — Problem Statement SIH26145**

Dummy FastAPI backend for the Irochi threat-detection system.

## Current Status

> **DUMMY / SCAFFOLD IMPLEMENTATION**
>
> This backend provides mock endpoints that return simulated data.
> No real Zeek, Redpanda, Redis, PostgreSQL, or ML is implemented.

## Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py     # GET /api/v1/health
│   │   │   ├── alerts.py     # GET /api/v1/alerts, /alerts/{id}
│   │   │   └── dashboard.py  # GET /api/v1/dashboard/summary
│   │   └── websocket/
│   │       ├── __init__.py
│   │       └── alerts.py     # WS /api/v1/ws/alerts
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── health.py         # Health response model
│   │   ├── alerts.py         # Alert models
│   │   └── dashboard.py      # Dashboard summary model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── alert_service.py  # Alert service interface + mock impl
│   │   └── dashboard_service.py  # Dashboard service interface + mock impl
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py         # Application configuration
│   └── mock/
│       ├── __init__.py
│       └── data.py           # Realistic mock alert data
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── test_health.py
│   ├── test_alerts.py
│   ├── test_dashboard.py
│   └── test_websocket.py
├── Dockerfile
├── requirements.txt
└── README.md                 # This file
```

## Run Locally

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/alerts` | List mock alerts |
| GET | `/api/v1/alerts/{alert_id}` | Get single mock alert |
| GET | `/api/v1/dashboard/summary` | Dashboard summary metrics |
| WS | `/api/v1/ws/alerts` | Live alert WebSocket (dummy) |

## Run Tests

```bash
cd backend
pytest tests/ -v
```
