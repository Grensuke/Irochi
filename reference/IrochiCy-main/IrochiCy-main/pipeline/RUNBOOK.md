# SIH26145 — Complete Pipeline Runbook

> Phase 3: Zeek → Normalizer → Feature Workers → Detectors → Alert Engine

---

## Prerequisites

- Phase 2 backend fully operational (`backend/RUNBOOK.md` complete)
- Docker Desktop running, all Phase 2 containers healthy
- Python 3.10+ installed
- `d:/SIH-145/infrastructure/.env` configured (copy from `.env.example`)

---

## First-Time Pipeline Setup

### Step 1: Download Datasets

**Option A: PCAPs (Recommended for full pipeline)**
```bash
cd d:/SIH-145/infrastructure
bash scripts/download_pcaps.sh
```
Manual: Download CICIDS2017 from https://www.unb.ca/cic/datasets/ids-2017.html
→ `Wednesday-workingHours.pcap` → `pcaps/cicids2017/`

**Option B: MachineLearningCVE CSV files**
If you only have the pre-computed CICFlowMeter CSV files (e.g., in `d:/SIH-145/MachineLearningCVE`), you can inject them directly into the normalizer, skipping Zeek entirely.
*Note: Because CSVs lack payload data and IP addresses, only the DDoS and Exfiltration detectors will trigger.*

### Step 2: Start all Docker services

```powershell
cd d:\SIH-145\infrastructure
docker compose up -d
docker compose ps   # All should be "healthy" within 60 seconds
```

### Step 3: Install Zeek packages (one time)

```bash
docker exec -it sih26145_zeek bash
bash /usr/local/zeek/share/zeek/site/install_packages.sh
exit
```

### Step 4: Create Redpanda topics (one time)

```bash
bash scripts/verify_topics.sh
# Should print 6 topic names at the end
```

### Step 5: Set up Python environment for pipeline

```powershell
cd d:\SIH-145\pipeline
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 6: Fetch SSLBL JA3 blacklist (one time, then auto-refreshes daily)

```powershell
python -c "import asyncio; from intel.sslbl import sslbl_feed; asyncio.run(sslbl_feed._fetch_and_cache())"
# Expect: "SSLBL feed updated, count=~5000"
```

### Step 7: Train ML models (takes 2-5 min each, one time)

```powershell
python -m models.ml.train_dns_dga
python -m models.ml.train_exfil
# Expect: classification report printed, models saved to models/ml/saved/
```

### Step 8: Verify Zeek works with a test PCAP

```bash
bash infrastructure/scripts/run_zeek_offline.sh /pcaps/ctu13/scenario1.pcap
# Expect: conn.log, dns.log, ssl.log generated
```

### Step 9: Run normalizer in batch mode (manual test)

**For Zeek PCAP logs:**
```powershell
python -m normalizer.normalizer --log-dir /zeek-logs/offline-* --mode batch
```

**For MachineLearningCVE CSV files:**
```powershell
python -m normalizer.normalizer --log-dir dummy --mode csv-batch --csv-dir ../MachineLearningCVE
```
*Expect: JSON output with non-zero "produced" count.*

### Step 10: Open Grafana and verify metrics

- URL: http://localhost:3000
- Login: `admin` / your `GRAFANA_PASSWORD`
- Pipeline Overview dashboard → events_per_second should be non-zero

---

## Daily Development Workflow (Full Stack)

```
Terminal 1 — Infrastructure:
  cd d:\SIH-145\infrastructure
  docker compose up -d

Terminal 2 — Backend (FastAPI):
  cd d:\SIH-145\backend
  .venv\Scripts\Activate.ps1
  uvicorn app.main:app --port 8000 --reload

Terminal 3 — Frontend:
  cd d:\SIH-145
  npm run dev

Terminal 4 — Process a PCAP (trigger detections):
  bash infrastructure/scripts/run_zeek_offline.sh /pcaps/ctu13/scenario1.pcap
```

Watch alerts appear live at http://localhost:5173/alerts

---

## Service URLs (Full Stack Running)

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Redpanda Console | http://localhost:8080 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

---

## Run ML Model Retraining

```powershell
# DNS/DGA — downloads new Bambenek feed, retrains
python -m models.ml.train_dns_dga

# Exfiltration — regenerates synthetic dataset, retrains
python -m models.ml.train_exfil
```

---

## Refresh SSLBL Blacklist Manually

```powershell
python -c "import asyncio; from intel.sslbl import sslbl_feed; asyncio.run(sslbl_feed._fetch_and_cache())"
```

Auto-runs daily if `sslbl_feed.ensure_loaded()` is called by the feature worker.

---

## Run All Pipeline Tests

```powershell
cd d:\SIH-145\pipeline

# Unit tests (no infrastructure needed)
pytest tests/ -v --ignore=tests/test_e2e_integration.py

# E2E integration (requires full stack running)
pytest tests/test_e2e_integration.py -v -s
```

---

## Run Full System Test (All Phases)

```powershell
# Phase 2 tests
cd d:\SIH-145\backend
python scripts/run_all_tests.py

# Phase 3 tests
cd d:\SIH-145\pipeline
pytest tests/ -v --ignore=tests/test_e2e_integration.py

# E2E integration
pytest tests/test_e2e_integration.py -v -s
```

---

## Grafana Dashboards

| Dashboard | Refresh | Key Panels |
|---|---|---|
| Pipeline Overview | 10s | EPS, events by type, normalizer throughput, dead letter, consumer lag |
| Detection Performance | 10s | Alerts/min by type, P95 latency, severity pie, detector status grid |
| System Health | 30s | FastAPI rate/latency, WebSocket, Redis, PostgreSQL, Redpanda |
| Network Traffic | 10s | Connection rate, protocol pie, top IPs, DNS vs alerts, TLS ratio |

---

## Troubleshooting

### "No brokers available" in normalizer or feature_worker
Redpanda not ready. `docker compose ps redpanda` → must be "healthy".
Wait 30 seconds after `docker compose up`, then retry.

### "conn.log not found" or empty
PCAP has no matching traffic, OR Zeek failed silently.
```bash
docker exec sih26145_zeek zeek --version   # Verify 6.0.4
```
Try: use `pcaps/ctu13/scenario1.pcap` (has all traffic types).

### "Warning: DNS/DGA model not found — using rule-based fallback"
```powershell
python -m models.ml.train_dns_dga
```
Detector still works via fallback — just lower accuracy.

### "SSLBL fetch failed"
No internet access from container. Run fetch from host:
```powershell
cd d:\SIH-145\pipeline
python -c "import asyncio; from intel.sslbl import sslbl_feed; asyncio.run(sslbl_feed._fetch_and_cache())"
```
Commit non-empty `intel/sslbl_cache.json` to repo as fallback.

### Feature worker producing 0 detections
Expected for clean/normal traffic. Use CTU-13 (contains malware).
```powershell
# Check events flowing
docker exec sih26145_redis redis-cli -a YOUR_PASSWORD get pipeline:events_per_second
# Check worker logs
docker logs sih26145_feature_worker
```

### Zeek JA3/JA4 fields all null
`install_packages.sh` not run inside Zeek container.
```bash
docker exec -it sih26145_zeek bash
bash /usr/local/zeek/share/zeek/site/install_packages.sh
```

### Normalizer processes 0 events
```bash
# Check log file format
docker exec sih26145_zeek head -10 /zeek-logs/*/conn.log
```
Should start with `#separator` lines, not JSON.
If JSON: set `redef LogAscii::use_json = F;` in `local.zeek`, reprocess.

### Grafana shows "No data"
Prometheus not scraping FastAPI. FastAPI must be running on port 8000.
```
http://localhost:9090/targets   # All targets should be UP
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PCAP / Live Interface                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│  Zeek 6.0.4 (Docker)                                               │
│  conn.log │ dns.log │ ssl.log                                      │
└──────┬────────┬────────┬───────────────────────────────────────────┘
       │        │        │
       ▼        ▼        ▼
┌────────────────────────────────────────────────────────────────────┐
│  Normalizer (Python)                                                │
│  ZeekLogReader → CanonicalEvent → Redpanda Producer                │
└──────┬────────┬────────┬───────────────────────────────────────────┘
       │        │        │
       ▼        ▼        ▼
┌────────────────────────────────────────────────────────────────────┐
│  Redpanda                                                           │
│  canonical.connection │ canonical.dns │ canonical.tls               │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│  Feature Worker (Python)                                            │
│  ┌──────────┐ ┌───────┐ ┌─────────┐ ┌────────┐ ┌───────┐         │
│  │ DDoS     │ │ Recon │ │ DNS/DGA │ │ TLS/C2 │ │ Exfil │         │
│  │ River+   │ │ Stats │ │ XGBoost │ │ SSLBL+ │ │ XGB   │         │
│  │ Rules    │ │       │ │ +Rules  │ │ Beacon │ │+Rules │         │
│  └──────────┘ └───────┘ └─────────┘ └────────┘ └───────┘         │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ DetectorResult
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│  Redpanda: detector.results                                        │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│  FastAPI Alert Engine (Phase 2)                                     │
│  → PostgreSQL (persistent)                                          │
│  → Redis Pub/Sub (live)                                             │
│  → WebSocket (React dashboard)                                      │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│  React Dashboard (localhost:5173)                                    │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────┐    │
│  │ Alert    │ │ Timeline │ │ KPI Cards │ │ WebSocket Live   │    │
│  │ Table    │ │          │ │           │ │ Notifications    │    │
│  └──────────┘ └──────────┘ └───────────┘ └──────────────────┘    │
└────────────────────────────────────────────────────────────────────┘

Observability: Prometheus → Grafana (4 dashboards)
```
