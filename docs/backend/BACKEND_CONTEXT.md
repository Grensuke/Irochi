# Backend Context — Vibhinetra

> **This file describes the CURRENT state of the backend.**
> It is NOT a conversation transcript. Update it after each approved checkpoint.

---

## Phase

E2E Real PCAP Validation Complete. All work packages and infrastructure integrations are verified against real network telemetry.

## Implementation Status

**Work Packages:**
- WP-A ✅ Infrastructure
- WP-B ✅ PostgreSQL
- WP-C ✅ Redpanda + Redis
- WP-D ✅ Feature / Window Engine
- WP-E ✅ Detector Framework
- WP-F ✅ PCAP, Recon, DDoS, DNS/DGA
- WP-G ✅ Alert Engine
- WP-H ✅ TLS/C2 Detector
- WP-I ✅ Exfiltration Detector (Now with XGBoost ML signal)
- WP-J ✅ Unknown Detector (Baseline & Z-Score)
- WP-K ✅ Incident Engine (Alert Correlation & Kill-Chain Tracking)
- WP-L ✅ ML Integration (River in DDoS, XGBoost in Exfil)
- EVALUATION ✅ Baseline Evaluation & Threshold Sensitivity completed
- SEVERITY ✅ Implemented dynamic, context-aware severity assignment across all 6 core detectors (eliminating MEDIUM hardcoded fallbacks).
- M8 = ✅ end-to-end MVP validation complete
- DEPLOYMENT-READY ✅ Pipeline processing bottleneck resolved (River JIT compilation globalized), sustaining 50+ flows/sec with <15ms detection latency for live continuous demonstration.
## Backend Structure

The backend is fully wired to actual infrastructure services:

- **Entry Point:** `app/main.py` instantiates and starts the `DetectionPipeline` during the FastAPI lifespan.
- **Streaming:** `KafkaConsumerService` handles real Redpanda messages.
- **State/Caching:** `FeatureEngine` relies on `RedisStateService`.
- **Detectors:** All 6 core detectors (`DdosDetector`, `ReconDetector`, `DnsDetector`, `C2Detector`, `ExfiltrationDetector`, `UnknownDetector`) are actively registered.
- **Alert Persistence:** `AlertEngine` saves to PostgreSQL via `PostgresAlertService`.
- **Incident Correlation:** `IncidentEngine` tracks multi-stage attacks and persists them via `PostgresIncidentService`.
- **Live Updates:** Alerts and Incidents are pushed through `RedisPubSubService`.
- **AI Analytics:** `ai_narrative.py` provides grounded threat storytelling based on deterministic evidence.
- **Schema Strictness:** Enforced explicit Enum typecasting in Alert API response schemas (`AlertResponse`).
- **Demo Infrastructure:** `live_demo.py` upgraded to consume `REDPANDA_BROKER` environment variable for dynamic deployments.

## Endpoints

| Method | Path | Status |
|---|---|---|
| GET | `/api/v1/health` | ✅ Working |
| GET | `/api/v1/alerts` | ✅ Working (Queries PostgreSQL) |
| GET | `/api/v1/alerts/{alert_id}` | ✅ Working (Queries PostgreSQL) |
| GET | `/api/v1/dashboard/summary` | ✅ Working (Queries PostgreSQL) |
| GET | `/api/v1/incidents` | ✅ Working (Queries PostgreSQL) |
| GET | `/api/v1/incidents/{incident_id}` | ✅ Working (Queries PostgreSQL) |
| WS | `/api/v1/ws/alerts` | ✅ Working (Backfill via DB, Live via Redis Pub/Sub) |
| WS | `/api/v1/ws/telemetry` | ✅ Working (Live flow and throughput stream via Redis Pub/Sub) |
| POST | `/api/v1/narrative/generate` | ✅ Working (Generates AI explanation) |

## Evaluation Tooling & Findings

**Evaluation Tools (`backend/tools/`):**
- `evaluate_detectors.py`: Core Level 1 (synthetic) and Level 2 (CIC-IDS2017) evaluation harness.
- `diagnostic_analysis.py`: Error profiles and packet rate distributions.
- `sensitivity_analysis.py`: Tests multiple thresholds against ground truth.
- `cross_validation.py`: Generalization testing across different day captures.

**Findings:**
- **DDoS Detector:** The default 1000 pps threshold misses low-bandwidth DoS attacks (e.g. Wednesday DoS Hulk). Candidate thresholds of 500-600 pps improve detection but introduce false positives in background traffic.
- **Recon Detector:** The default 50 ports threshold is sensitive but generates false positives. Candidate threshold of 900 ports improves precision but requires more tuning.
- **Flow/Window Distortion:** Reconstructing flows from PCAP causes artificial burstiness due to missing real-time inter-arrival spacing, heavily penalizing simple rate-based detection.
- **E2E Real PCAP Audit:** Verified primary ML models (DGA, C2, Exfiltration) are fully active. The `UnknownDetector` successfully acts as a powerful statistical baseline fallback (catching extreme volumetric and port scan deviations). Incident engine successfully correlates cross-detector alerts into unified entity events.

**Note:** The production defaults remain 1000 pps and 50 ports. Candidate thresholds are currently evaluation outputs, not finalized rules. See [`docs/EVALUATION.md`](../EVALUATION.md) for the full methodology and findings.

## Known Constraints / Limitations

- DGA (`DnsDetector`) strictly relies on an external `.joblib` model artifact to run.
- Production authentication (JWT + RBAC + Argon2) is pending.
- Real NetFlow/IPFIX adapter is pending.
- Stale-update concurrency in Alert Engine requires review under load.
