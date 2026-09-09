# Backend Context — Irochi

> **This file describes the CURRENT state of the backend.**
> It is NOT a conversation transcript. Update it after each approved checkpoint.

---

## Phase

Active Infrastructure & Detector Evaluation. WP-G (Alert Engine) and base infrastructure integration are completed.

## Implementation Status

**Work Packages:**
- WP-A ✅ Infrastructure
- WP-B ✅ PostgreSQL
- WP-C ✅ Redpanda + Redis
- WP-D ✅ Feature / Window Engine
- WP-E ✅ Detector Framework
- WP-F ✅ PCAP, Recon, DDoS, DNS/DGA
- WP-G ✅ Alert Engine
- WP-H = PENDING
- WP-I = PENDING
- EVALUATION ✅ Baseline Evaluation & Threshold Sensitivity completed
- M8 = IN PROGRESS — end-to-end MVP validation

## Backend Structure

The backend is fully wired to actual infrastructure services:

- **Entry Point:** `app/main.py` instantiates and starts the `DetectionPipeline` during the FastAPI lifespan.
- **Streaming:** `KafkaConsumerService` handles real Redpanda messages.
- **State/Caching:** `FeatureEngine` relies on `RedisStateService`.
- **Detectors:** `DdosDetector` (1000 pps), `ReconDetector` (50 ports), and `DnsDetector` (DGA via `.joblib`) are actively registered.
- **Alert Persistence:** `AlertEngine` saves to PostgreSQL via `PostgresAlertService`.
- **Live Updates:** Alerts are pushed through `RedisPubSubService`.

## Endpoints

| Method | Path | Status |
|---|---|---|
| GET | `/api/v1/health` | ✅ Working |
| GET | `/api/v1/alerts` | ✅ Working (Queries PostgreSQL) |
| GET | `/api/v1/alerts/{alert_id}` | ✅ Working (Queries PostgreSQL) |
| GET | `/api/v1/dashboard/summary` | ✅ Working (Queries PostgreSQL) |
| WS | `/api/v1/ws/alerts` | ✅ Working (Backfill via DB, Live via Redis Pub/Sub) |

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

**Note:** The production defaults remain 1000 pps and 50 ports. Candidate thresholds are currently evaluation outputs, not finalized rules. See [`docs/EVALUATION.md`](../EVALUATION.md) for the full methodology and findings.

## Known Constraints / Limitations

- DGA (`DnsDetector`) strictly relies on an external `.joblib` model artifact to run.
- Production authentication (JWT + RBAC + Argon2) is pending.
- Real NetFlow/IPFIX adapter is pending.
- Stale-update concurrency in Alert Engine requires review under load.
