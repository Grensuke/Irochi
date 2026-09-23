# SIH26145 Pipeline — Network Traffic Normalizer

Phase 3 of SIH26145: Zeek-based network traffic capture and normalization pipeline.

## Architecture

```
PCAP / Live Interface
        │
        ▼
   ┌─────────┐    Zeek TSV Logs    ┌────────────┐    Canonical Events    ┌──────────┐
   │  Zeek    │ ──────────────────▶ │ Normalizer │ ─────────────────────▶ │ Redpanda │
   │ (Docker) │   conn.log          │  (Python)  │   canonical.connection │          │
   └─────────┘   dns.log            └────────────┘   canonical.dns        └──────────┘
                 ssl.log                              canonical.tls
                                                      dead.letter
```

## Prerequisites

- Docker Desktop running with services from `infrastructure/docker-compose.yml`
- Python 3.10+
- Redpanda on `localhost:9092`
- Redis on `localhost:6379`

## Quick Start

### 1. Start Infrastructure

```bash
cd infrastructure
docker compose up -d
```

### 2. Create Redpanda Topics

```bash
bash infrastructure/scripts/verify_topics.sh
```

### 3. Set Up Pipeline Environment

```powershell
cd pipeline
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run Tests

```bash
cd pipeline
pytest tests/ -v
```

## Zeek Setup

### Install JA3/JA4 Packages (inside container)

```bash
docker exec sih26145_zeek bash /usr/local/zeek/share/zeek/site/install_packages.sh
```

### Download PCAPs

```bash
bash infrastructure/scripts/download_pcaps.sh
```

### Offline Analysis

```bash
bash infrastructure/scripts/run_zeek_offline.sh /pcaps/ctu13/scenario1.pcap
```

### Live Capture

```bash
bash infrastructure/scripts/run_zeek_live.sh eth0
```

### Smoke Test

```bash
docker exec sih26145_zeek bash /usr/local/zeek/share/zeek/site/test_zeek.sh
```

## Normalizer Usage

### Batch Mode (one-shot)

```bash
python -m normalizer.normalizer --log-dir /path/to/zeek/logs --mode batch
```

### Watch Mode (continuous)

```bash
python -m normalizer.normalizer --log-dir /path/to/zeek/logs --mode watch
```

### Dry Run (stats only, no Redpanda)

```bash
python -m normalizer.normalizer --log-dir /path/to/zeek/logs --stats-only
```

## Redpanda Topics

| Topic | Partitions | Retention | Key | Publisher → Consumer |
|---|---|---|---|---|
| `canonical.connection` | 4 | 1 hour | `src_ip` | Normalizer → Feature Worker |
| `canonical.dns` | 4 | 1 hour | `src_ip` | Normalizer → Feature Worker |
| `canonical.tls` | 2 | 1 hour | `src_ip` | Normalizer → Feature Worker |
| `detector.results` | 2 | 2 hours | `threat_type` | Feature Worker → Alert Engine |
| `dead.letter` | 1 | 24 hours | `original_topic` | Any → Manual Inspection |
| `pipeline.metrics` | 1 | 1 hour | `metric_name` | Workers → Dashboard |

## Canonical Event Schema

Version: `1.0.0`

All events share a common envelope (`CanonicalEnvelope`) with event-type-specific payloads.

### Envelope Fields

- `event_id` — UUID (auto-generated)
- `event_type` — `"connection"`, `"dns"`, or `"tls"`
- `connection_id` — Zeek UID
- `timestamp` — Epoch microseconds (int64)
- `ingest_timestamp` — Auto-generated at emit time
- `sensor_source` — `"zeek"`, `"netflow"`, `"ipfix"`, `"sflow"`
- `src_ip`, `dst_ip` — Validated IP addresses
- `src_port`, `dst_port` — 0-65535
- `protocol` — `"tcp"`, `"udp"`, `"icmp"`, `"other"`
- `schema_version` — `"1.0.0"`

## Test Fixtures

- `tests/fixtures/sample_conn.log` — 20 rows: SF, S0, REJ, RSTO, UDP, ICMP, exfil simulation, DDoS simulation
- `tests/fixtures/sample_dns.log` — 20 rows: A, AAAA, TXT, MX, DGA domains, NXDOMAIN, SERVFAIL, DNS tunneling
- `tests/fixtures/sample_ssl.log` — 20 rows: TLS 1.3/1.2, JA3/JA3s, self-signed certs, failed handshakes
