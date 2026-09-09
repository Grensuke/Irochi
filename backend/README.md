# Irochi — Backend

**SIH 2026 — Problem Statement SIH26145**

Backend for the Irochi threat-detection system. This is a real-time, streaming pipeline built with Python, FastAPI, and asynchronous consumers.

## Current Status

> **ACTIVE INFRASTRUCTURE**
>
> This backend is fully integrated with Redpanda (ingest), PostgreSQL (persistence), and Redis (hot state & pub/sub).
> It serves real alerts to the frontend via REST and WebSocket endpoints.

## Architecture & Runtime Pipeline

The backend is instantiated within the FastAPI application lifespan. The primary components are:

1. **FastAPI Application**: Serves REST endpoints and WebSocket connections.
2. **KafkaConsumerService**: Streams `CanonicalEvent` messages from Redpanda.
3. **FeatureEngine & WindowManager**: Aggregates network flows into sliding/tumbling windows or enriched entities, using `RedisStateService` for distributed hot state.
4. **DetectorRouter**: Evaluates `FeatureRecords` against active detector models.
5. **AlertEngine**: Persists detected threats (`Decision.DETECTION`) into PostgreSQL and publishes them to Redis Pub/Sub for live clients.

## Active Detectors

- **DDoS Detector**: Volumetric threshold-based detector. (Active, default 1000 pps)
- **Recon Detector**: Port-scan uniqueness threshold detector. (Active, default 50 ports)
- **DNS/DGA Detector**: ML-based DGA classification using River/XGBoost. *(Requires external `.joblib` model artifact to function at runtime)*

*Note: TLS/C2 and Exfiltration detectors are planned but not currently active.*

## Endpoints

| Method | Path | Description | Status |
|---|---|---|---|
| GET | `/api/v1/health` | Health check | Active |
| GET | `/api/v1/alerts` | List historical alerts from DB | Active |
| GET | `/api/v1/alerts/{alert_id}` | Get single alert from DB | Active |
| GET | `/api/v1/dashboard/summary` | Global threat/telemetry summary | Active |
| WS | `/api/v1/ws/alerts` | Live alert WebSocket stream | Active |

## Structure

```text
backend/
├── app/
│   ├── main.py              # FastAPI application & pipeline orchestrator
│   ├── api/                 # REST & WebSocket endpoints
│   ├── schemas/             # Pydantic data models (Events, Features, Alerts)
│   ├── services/
│   │   ├── stream/          # Kafka/Redpanda consumer logic
│   │   ├── state/           # Redis state management
│   │   ├── features/        # Window and enrichment processing
│   │   ├── detectors/       # Threat detection modules
│   │   └── alerts/          # Alert persistence and pub/sub
│   ├── core/                # Configuration and dependencies
│   └── mock/                # Legacy mock data generators (kept for validation)
├── tools/                   # Evaluation & Diagnostic Tooling (Level 2)
├── tests/                   # Unit and integration tests
├── Dockerfile
├── requirements.txt
└── README.md                # This file
```

## Running with Docker (Recommended)

The backend is configured to run inside a Docker container orchestrated by the root `docker-compose.yml`.

```bash
cd ..
docker compose up backend
```

## Running Locally

If you need to run the backend bare-metal (e.g. for debugging):

```bash
cd backend
python -m venv .venv

# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
*(Ensure your `.env` correctly points to your local or Docker infrastructure for Redis, PostgreSQL, and Redpanda).*

## Testing & Evaluation

### Automated Tests
Run standard unit and integration tests using pytest:
```bash
pytest tests/ -v
```

### End-to-End Validation (Level 1)
To run the deterministic detector boundary evaluations:
```bash
python tools/evaluate_detectors.py
```

### Dataset Evaluation (Level 2)
Extensive offline evaluation tooling is provided to validate the detectors against the external CIC-IDS2017 dataset.

- `evaluate_detectors.py` (Level 2)
- `diagnostic_analysis.py`
- `sensitivity_analysis.py`
- `cross_validation.py`

See [`docs/EVALUATION.md`](../docs/EVALUATION.md) for the full evaluation methodology, limitations, and baseline results.
