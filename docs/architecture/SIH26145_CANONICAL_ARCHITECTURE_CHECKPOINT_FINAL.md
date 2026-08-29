# SIH26145 — CANONICAL ARCHITECTURE CHECKPOINT

> **Purpose**
>
> This document is the single recovery/reference point for the SIH26145 architecture discussion completed so far. It records what is **locked**, what is **conditional/not yet finalized**, why the major decisions were made, the exact component order, the important implementation invariants, and the next design task.
>
> **Important:** Do not re-litigate locked architecture decisions unless a later benchmark, requirement, or verified source provides a concrete reason to change them. Conditional items must remain conditional until their stated decision point.

---

# 1. Project Understanding

SIH26145 is being approached as a **passive, real-time network threat-detection and security-intelligence system**.

The system observes traffic through a monitoring environment, converts traffic/flow observations into structured telemetry, derives behavioural features, uses rules and machine-learning models to detect suspicious activity, creates explainable security alerts, persists important information, and delivers live alerts to a security analyst dashboard.

The system is **not an inline firewall** and is not designed around sending packets back into or actively probing the monitored production network.

The central idea is:

```text
Observe
  ↓
Normalize
  ↓
Stream
  ↓
Extract behavioural features
  ↓
Detect threats
  ↓
Score + explain
  ↓
Persist alert
  ↓
Notify analyst
```

---

# 2. Locked Technology Stack

## Frontend

```text
React
Vite
TypeScript
```

Role:

- Analyst-facing security dashboard.
- Consumes backend REST APIs.
- Receives live updates through WebSockets.
- Does not directly access PostgreSQL, Redis, or Redpanda.

---

## Backend

```text
Python
FastAPI
```

Role:

- Application/API layer.
- Authentication and authorization.
- REST endpoints.
- WebSocket endpoints.
- Dashboard data access.
- Frontend integration.

FastAPI is **not** the primary high-volume packet-processing engine.

---

## Network Telemetry

```text
Zeek
Python Ingest Normalizer
```

Role:

- Zeek = network observation/protocol telemetry.
- Normalizer = converts telemetry from different sources into a source-independent canonical representation.

---

## Streaming

```text
Redpanda
```

Role:

- Internal event-stream transport.
- Decouples ingestion, feature processing, detection, and other backend stages.

Exact topic names/topology are **not yet finalized**.

---

## AI / ML

```text
Scikit-learn
XGBoost
River
```

Role:

- Scikit-learn: preprocessing, evaluation, utilities, and selected models.
- XGBoost: supervised, feature-rich/tabular detection where appropriate.
- River: online/streaming-learning models where adaptive sequential learning is useful.

The architecture uses **threat-specific detectors**, not one giant universal classifier.

Rules/statistics may also be used where they are more appropriate than ML.

---

## Hot State

```text
In-memory Python/River state
Redis
```

Two distinct Redis uses:

```text
Redis Data Structures
→ shared hot state

Redis Pub/Sub
→ live alert fan-out
```

Do **not** route every event through Redis.

---

## Persistent Storage

```text
PostgreSQL
```

TimescaleDB is **conditional**, not locked:

```text
PostgreSQL
   ↓
database schema + volume + retention + query analysis
   ↓
decide whether selected time-heavy tables benefit from TimescaleDB
```

Do not add TimescaleDB simply because Prometheus stores time-series metrics; Prometheus is a separate metrics system.

---

## Real-time

```text
WebSockets
```

Role:

- Backend-to-browser live delivery of alerts and live dashboard state.

---

## Security

```text
JWT
RBAC
Argon2
```

- JWT = authentication/session token mechanism.
- RBAC = role-based permissions.
- Argon2 = password hashing.

Keep identity management lightweight for the SIH prototype unless requirements later justify a dedicated identity platform.

---

## Infrastructure

```text
Docker
Docker Compose
```

Role:

- Reproducible local/demo environment.
- Runs the multi-component stack consistently.

Do not introduce Kubernetes for the current laptop-based SIH prototype.

---

## Observability

```text
Structured JSON logging
Prometheus
Grafana
```

Prometheus measures metrics such as:

```text
flows/sec
events/sec
processing latency
detection latency
queue lag
dropped events
alerts/sec
WebSocket connections
CPU
RAM
```

Grafana is for infrastructure/developer monitoring.

The React application remains the analyst-facing security dashboard.

---

# 3. Complete End-to-End Architecture

```text
                         INGESTION
                            |
          +-----------------+------------------+
          |                                    |
          v                                    v
 PCAP / LIVE PACKETS                    NetFlow / IPFIX
          |                                    |
          v                                    |
        ZEEK                                   |
          |                                    |
          v                                    |
   Zeek structured logs                        |
 (conn/dns/ssl/etc.)                           |
          |                                    |
          +------------------+-----------------+
                             |
                             v
                    INGEST NORMALIZER
                             |
                             v
                         REDPANDA
                             |
                             v
                    FEATURE PROCESSING
                       ↙           ↘
              In-memory State     Redis
             per-worker state    shared hot state
                       ↘           ↙
                             v
                         DETECTORS
       +----------+----------+----------+----------+----------+
       |          |          |          |          |
       v          v          v          v          v
      DDoS      Recon      DNS/DGA/    TLS/C2   Exfiltration
     Detector  Detector   DNS-Tunnel   Detector    Detector
                           Detector
       |          |          |          |          |
       +----------+----------+----------+----------+
                             |
                             v
                     SCORED DETECTIONS
                             |
                             v
                       ALERT ENGINE
                             |
                             v
                     CREATE ALERT ID
                             |
                             v
                  INSERT INTO POSTGRESQL
                             |
                             v
                       AWAIT COMMIT
                             |
                     COMMIT SUCCESS?
                       /          \
                    NO              YES
                    |                |
                    v                v
              LOG / RETRY       REDIS PUB/SUB
             DO NOT PUBLISH     live notification
                                     |
                         +-----------+-----------+
                         |           |           |
                         v           v           v
                     FastAPI A   FastAPI B   FastAPI C
                         |           |           |
                         v           v           v
                     WebSocket   WebSocket   WebSocket
                         |           |           |
                         +-----------+-----------+
                                     |
                                     v
                              React + Vite
                               + TypeScript
```

Prometheus and Grafana operate alongside the system.

---

# 4. What Each Layer Means

A useful mental model:

```text
Zeek
= "What happened on the network?"

Normalizer
= "Put different telemetry sources into one language."

Redpanda
= "Move events through the backend."

Feature Processing
= "What measurable behaviour can we derive?"

Detectors
= "Does the behaviour look suspicious?"

Alert Engine
= "What should the analyst be told?"

PostgreSQL
= "What definitely happened and must be remembered?"

Redis
= "What hot/shared state or live notification is needed right now?"

FastAPI
= "How does the application expose the information?"

WebSocket
= "How do live updates reach the browser?"

React
= "How does the analyst see and interact with the information?"
```

---

# 5. Critical Raw-vs-Derived Boundary

This rule is **locked**.

> **Canonical Event = observed/normalized facts.**
>
> **Feature/Window Schema = calculated/derived values.**
>
> **Detector Result = interpretation/classification.**
>
> **Alert = analyst-facing security record.**

Example:

```text
RAW / CANONICAL
----------------
src_ip
dst_ip
src_port
dst_port
orig_bytes
resp_bytes
orig_pkts
resp_pkts
query
qtype
ja3
ja4
timestamp
```

then:

```text
DERIVED / FEATURE
-----------------
source_ip_entropy
domain_entropy
packet_rate
syn_ratio
beacon_periodicity
query_frequency
ja3_blacklist_match
outbound_inbound_ratio
UDP asymmetry/amplification metric
```

then:

```text
DETECTOR RESULT
---------------
threat_type
confidence
detector_id
evidence
```

then:

```text
FINAL ALERT
-----------
alert_id
timestamp
threat_type
severity
confidence
evidence
status
model_version
...
```

This separation prevents derived/windowed values from being mistaken for raw observations.

---

# 6. Telemetry Sources

## Zeek

Core logs of interest:

```text
conn.log
dns.log
ssl.log
```

plus other relevant logs where required by an explicitly installed package.

Zeek is the primary packet/protocol telemetry engine.

---

## NetFlow/IPFIX

NetFlow/IPFIX is alternate flow telemetry.

It goes:

```text
NetFlow/IPFIX
      ↓
Normalizer
```

not:

```text
NetFlow/IPFIX
      ↓
Zeek
```

The downstream processing should remain source-independent.

---

# 7. Zeek Version and Package Decisions

## Zeek Version

Target:

> **Zeek 6+**

This is required by the selected JA4 package plan for the desired QUIC support.

## Version Pinning

Do **not** use an unpinned `latest` tag for the demo/development environment.

Use:

```text
a specific tested Zeek tag
or
a fixed tested patch version
```

For example, a tested LTS tag is acceptable if that exact tag has been validated by the team.

The goal is:

```text
reproducible Zeek + package behaviour
```

not moving behaviour from an unpinned latest image.

---

## JA3 / JA4 Package Dependency

Do not assume core Zeek supplies all JA3/JA4 fingerprints automatically.

The project should explicitly install and test the selected Zeek fingerprint packages.

Current design:

```text
Zeek
 |
 +-- core conn/dns/ssl telemetry
 |
 +-- explicit JA3 support
 |
 +-- explicit JA4/JA4+ support
```

The exact package/version should be pinned and tested as part of the Dockerized demo environment.

---

# 8. Ingestion Modes

## Primary SIH Demo

```text
PCAP
  ↓
tcpreplay
  ↓
monitored interface
  ↓
Zeek (live capture)
  ↓
Normalizer
```

Why:

- preserves temporal pacing,
- makes the demo look like traffic is arriving live,
- allows alerts to appear progressively instead of dumping a wall of results.

## Development / Debug

```text
PCAP
  ↓
zeek -r
  ↓
offline logs
```

Why:

- repeatable,
- convenient for debugging,
- useful for deterministic log generation and feature development.

## Future Deployment

```text
Live interface
  ↓
Zeek (live)
```

---

# 9. Feature Processing and Windows

Feature Processing is responsible for deriving behavioural features from normalized events.

Examples:

```text
packet_rate
byte_rate
syn_ratio
source_ip_entropy
domain_entropy
unique_destination_ports
unique_destination_hosts
beacon_periodicity
query_frequency
outbound_inbound_ratio
windowed transfer volume
TLS fingerprint match/reputation
```

Many features require time windows.

Examples:

```text
DDoS
→ rolling rates

C2
→ inter-arrival times + periodicity

Recon
→ unique ports/hosts over a window

Exfiltration
→ rolling transfer volume/asymmetry

DNS
→ query frequency/distribution
```

The exact window lengths are **not yet finalized**.

---

# 10. Hybrid State Architecture

## In-memory

Use for:

- ultra-hot per-worker calculations,
- rolling state,
- River model state,
- frequent local calculations that do not need cross-worker sharing.

## Redis Data Structures

Use for:

- shared rolling counters,
- short-lived sets,
- cross-worker state,
- hot dashboard metrics.

## Redis Pub/Sub

Separate Redis function:

```text
Alert Engine
      ↓
Redis Pub/Sub
      ↓
multiple FastAPI workers
```

This is for live alert fan-out.

Redis Pub/Sub is **not** durable storage.

---

# 11. Detector Architecture

There are **five logical detector modules**:

```text
1. DDoS Detector
2. Recon Detector
3. DNS/DGA/DNS-Tunneling Detector
4. TLS/C2 Detector
5. Exfiltration Detector
```

These are logically distinct modules.

They do **not** need to be separate microservices.

A single Python detection worker or a small number of workers can host multiple detector modules.

Do not create one container/service per threat unless future benchmark results prove that separate scaling is necessary.

---

# 12. Threat-to-Signal Decisions

## 12.1 Volumetric DDoS

Raw telemetry needed:

```text
src_ip
dst_ip
src_port
dst_port
protocol
timestamp
orig_pkts
resp_pkts
orig_bytes
resp_bytes
TCP state/history where available
```

Derived candidates:

```text
packet_rate
byte_rate
syn_ratio
source_ip_entropy
UDP asymmetry/amplification metrics
```

### UDP Amplification is NOT finalized

Potential derived formulations:

```text
amplification_ratio
unsolicited_response_rate
large_udp_response_rate
response/request byte asymmetry
reflector-source-port indicators
```

The final formula depends on the actual **sensor/PCAP observation point**.

If both request and response legs are observed, a request/response amplification ratio may be meaningful.

If the capture is victim-side, the original spoofed request may not be visible; in that case unsolicited large-response rate/asymmetry may be more appropriate.

Do not lock `amplification_ratio` into the final Feature/Window Schema before reviewing the actual demo PCAP.

---

## 12.2 C2 Beaconing

Raw telemetry:

```text
connection timestamps
source/destination
repeated connection events
```

Derived:

```text
inter_arrival_time
periodicity
periodicity variance
regularity
repeated-destination behaviour
connection frequency
```

Important:

> C2 beaconing is a **general flow/timing signal**, not a TLS-only signal.

It should therefore be able to operate on general connection/flow events.

---

## 12.3 DGA / DNS Tunneling

Raw DNS telemetry:

```text
query
qtype
qtype_name
rcode
rcode_name
answers
DNS endpoints
timestamp
```

Derived:

```text
query_length
domain_entropy
label-length statistics
n_gram / lexical score
query_frequency
record_type distribution
```

Do not use a vague feature called simply:

```text
entropy
```

Use explicit names:

```text
domain_entropy
source_ip_entropy
```

because these represent different measurements.

DGA and DNS tunneling remain within the same logical DNS detector module but can use different feature sets/models.

---

## 12.4 Encrypted-session Malware

### MVP decision

Primary working signal:

```text
JA3 fingerprint
      ↓
SSLBL intelligence / blacklist
      ↓
ja3_blacklist_match
```

Important:

> A JA3 blacklist match is a **derived intelligence signal**, not a raw fact.

The raw canonical event contains:

```text
ja3
```

while the feature layer contains:

```text
ja3_blacklist_match
```

### SSLBL caution

SSLBL's blacklist is based on malware PCAP observations and is not equivalent to a universally validated classifier against benign traffic.

Therefore:

```text
ja3_blacklist_match
```

should be treated as a **medium-confidence supporting signal**, not an automatic conviction.

The Alert Engine should combine it with other evidence.

### JA4 / JA4S

Use:

```text
JA4
JA4S
```

as supplementary TLS fingerprint metadata and investigation features in the MVP.

Do not assume a JA4 intelligence feed has the same maturity/availability as SSLBL's JA3 blacklist.

### Stretch

Later, optionally add:

```text
packet sizes
packet directions
inter-packet timing
sequence/statistical features
```

for encrypted-traffic anomaly detection.

This is stretch work, not a core dependency.

---

# 13. JA4+ Multiple-Log Rule

Do **not** collapse all JA4+ information into one generic field such as:

```text
tls_fingerprint
```

Different JA4+ variants can originate from different Zeek logs.

Therefore the schema must preserve the distinction between the actual observed fingerprint fields/log provenance.

This must be handled during the Canonical Event Schema matrix.

---

# 14. Reconnaissance / Port Scanning

Raw:

```text
source IP
destination IP
destination port
timestamp
```

Derived:

```text
unique_destination_ports
unique_destination_hosts
connection_fan_out
scan_rate
```

This is naturally windowed.

---

# 15. Data Exfiltration

Raw directional telemetry:

```text
originator
responder
orig_bytes
resp_bytes
orig_pkts
resp_pkts
duration
source/destination
timestamp
```

Derived:

```text
outbound_inbound_ratio
byte_rate
windowed transfer volume
large-transfer indicators
```

Use Zeek-aligned:

```text
originator
responder
```

for raw directional semantics rather than ambiguously calling raw fields inbound/outbound.

---

# 16. IP / Port Naming Convention

The Canonical Event Schema is source-independent, so IP/port fields should use:

```text
src_ip
dst_ip
src_port
dst_port
```

However, directional byte/packet fields use:

```text
orig_bytes
resp_bytes
orig_pkts
resp_pkts
```

to preserve Zeek's explicit originator/responder semantics.

This is intentional, not an inconsistency.

Later feature definitions will explicitly map originator/responder into any application-level inbound/outbound interpretation.

---

# 17. AI / ML Strategy

The system uses a **hybrid detection strategy**:

```text
Rules / Statistics
        +
XGBoost
        +
River
        +
Scikit-learn utilities/models
```

Principles:

- Do not force every threat into ML.
- Do not force every threat into XGBoost.
- Do not force every threat into River.
- Use threat-specific feature sets.
- Use the simplest effective method for each threat.
- Use River where online/adaptive learning is genuinely useful.
- Use XGBoost where feature-rich supervised tabular classification is appropriate.

---

# 18. Alert Engine

The Alert Engine converts detector outputs into standardized analyst-facing alerts.

Responsibilities:

```text
confidence
severity
evidence
deduplication
correlation
final alert creation
persistent write ordering
live publication after commit
```

Basic flow:

```text
Detector Result
     ↓
Alert Engine
     ↓
Create alert ID
     ↓
Persist alert to PostgreSQL
     ↓
AWAIT COMMIT
     ↓
Publish live signal via Redis Pub/Sub
```

---

# 19. Alert Write Ordering Invariant

This is **locked**.

```text
Alert Engine
     ↓
Create Alert ID
     ↓
PostgreSQL INSERT
     ↓
AWAIT COMMIT
     ↓
Commit successful?
   /             \
 NO               YES
 |                 |
 v                 v
log/retry      Redis Pub/Sub
do not publish  live notification
```

Rule:

> **An alert must be successfully committed to PostgreSQL before its ID/message is published to Redis Pub/Sub.**

This prevents a WebSocket client from receiving an alert notification before its durable record exists.

PostgreSQL remains the authoritative persistent source of truth.

---

# 20. Redis Pub/Sub Reliability Model

Redis Pub/Sub is a **best-effort live notification channel**, not durable event history.

Possible case:

```text
PostgreSQL commit ✅
Redis publish ❌
```

The alert still exists in PostgreSQL.

That is safe because the frontend has a reconciliation path.

---

# 21. WebSocket Fan-out

Live path:

```text
Alert Engine
      ↓
Redis Pub/Sub
      ↓
+-----+-----+-----+
|     |     |     |
v     v     v
FastAPI A FastAPI B FastAPI C
|     |     |
v     v     v
WS    WS    WS
|     |     |
+-----+-----+
     |
     v
 React clients
```

Do not expose Redis Pub/Sub directly to the browser.

---

# 22. WebSocket Reconnect / Backfill

Because Redis Pub/Sub can lose messages for disconnected subscribers, reconnect must use PostgreSQL as the recovery source.

```text
React connect/reconnect
          ↓
REST backfill request
          ↓
PostgreSQL
          ↓
recover alerts after saved cursor
          ↓
resume live WebSocket stream
```

The exact cursor format is **not yet finalized**.

Candidate: a stable alert identifier/cursor rather than relying only on timestamps.

The architectural invariant is:

> **PostgreSQL backfill provides recovery; Redis Pub/Sub provides live notification.**

---

# 23. PostgreSQL / TimescaleDB Decision

Current decision:

```text
PostgreSQL = LOCKED

TimescaleDB = CONDITIONAL
```

Evaluate TimescaleDB during the PostgreSQL schema stage using:

```text
actual data volume
retention period
time-range query patterns
historical alert/event volume
```

Do not add TimescaleDB solely because Prometheus stores time-series metrics.

Only selected time-heavy tables should potentially use TimescaleDB if the analysis justifies it.

---

# 24. FastAPI Responsibilities

FastAPI provides:

```text
authentication
authorization
REST endpoints
WebSocket endpoints
dashboard queries
user operations
frontend integration
```

Typical future endpoint categories may include:

```text
/auth/*
/alerts/*
/dashboard/*
/threats/*
/users/*
/ws/*
```

Exact routes are **not finalized yet**.

---

# 25. Authentication

Conceptual flow:

```text
React
  ↓
Login
  ↓
FastAPI
  ↓
verify credentials
  ↓
JWT
  ↓
authenticated REST/WebSocket access
```

Example roles:

```text
ADMIN
ANALYST
```

Exact permissions are not finalized yet.

---

# 26. Docker / Compose

A conceptual local/demo environment:

```text
Docker Compose
|
+-- FastAPI
+-- Detection Worker(s)
+-- Zeek
+-- Redpanda
+-- Redis
+-- PostgreSQL
+-- Prometheus
+-- Grafana
```

The frontend may also be containerized later, but its development should not depend on the backend infrastructure container layout.

---

# 27. Observability

Structured application/service logs should capture enough information to diagnose pipeline failures.

Metrics should make the SIH performance claim measurable:

```text
flows/sec
events/sec
processing latency
detection latency
queue lag
dropped events
alerts/sec
CPU
RAM
WebSocket connections
```

Do not state a throughput capability until it is actually benchmarked.

**Candidate benchmark target:** approximately:

```text
100 Mbps
~5,000 flows/sec
```

These are **validation targets, not locked requirements**, until their provenance is confirmed against the official SIH26145 problem statement or another authoritative team source.

---

# 28. Demo Strategy

Primary demo:

```text
recorded PCAP
      ↓
tcpreplay
      ↓
monitored interface
      ↓
Zeek live
      ↓
Normalizer
      ↓
Redpanda
      ↓
Feature Processing
      ↓
Detectors
      ↓
PostgreSQL
      +
Redis Pub/Sub
      ↓
FastAPI
      ↓
WebSocket
      ↓
React dashboard
```

Development/debug path:

```text
PCAP
 ↓
zeek -r
 ↓
logs
```

This dual-mode design gives repeatability during development while preserving a live-looking progressive demo.

---

# 29. Architecture Rules / Invariants

1. Do not make every detector a separate microservice.
2. Do not send every event through Redis.
3. Do not use PostgreSQL as the event bus.
4. Do not expose Redis, PostgreSQL, or Redpanda directly to React.
5. Do not force NetFlow/IPFIX through Zeek.
6. Do not force every threat into one ML model.
7. Do not claim throughput until it is benchmarked on the actual demo setup.
8. Do not publish an alert to Redis Pub/Sub until its PostgreSQL transaction has committed successfully.
9. Treat Redis Pub/Sub as best-effort live notification; use PostgreSQL REST backfill to recover missed alerts.
10. Keep raw observed fields separate from derived/windowed features.
11. Do not treat `amplification_ratio` as finalized until the actual PCAP vantage point is reviewed.
12. Use JA3 + SSLBL as the primary encrypted-session malware MVP signal.
13. Treat `ja3_blacklist_match` as a supporting/medium-confidence signal rather than a hard conviction.
14. Treat JA4/JA4S as supplementary metadata in the MVP.
15. Do not assume all JA4+ variants live in one Zeek log or one generic TLS fingerprint field.
16. Keep C2 beaconing independent of TLS.
17. Use explicit entropy names such as `source_ip_entropy` and `domain_entropy`.
18. Prefer `src_*` / `dst_*` for source-independent IP/port fields and Zeek-aligned `orig_*` / `resp_*` for directional packet/byte fields.
19. Pin Zeek to a specific tested tag/version; never run the demo/dev environment on unpinned `latest`.
20. Standardize the project on a tested Zeek 6+ environment.
21. Primary SIH demo uses tcpreplay through a monitored interface; `zeek -r` remains the dev/debug path.
22. Do not commit the UDP amplification feature formula until the actual PCAP/sensor vantage point is reviewed.
23. Do not add TimescaleDB unless database schema/retention/data-volume/query analysis justifies it.
24. Keep PostgreSQL as durable alert truth even when Redis Pub/Sub is used for live fan-out.
25. On WebSocket reconnect, perform database backfill before relying on the live stream.

---

# 30. Locked vs Conditional Decisions

## LOCKED

- React + Vite + TypeScript
- Python + FastAPI
- Zeek + Python Ingest Normalizer
- NetFlow/IPFIX direct-to-Normalizer
- Redpanda as internal event transport
- Scikit-learn + XGBoost + River
- threat-specific detector modules
- hybrid in-memory + Redis hot state
- Redis data structures for shared hot state
- Redis Pub/Sub for live alert fan-out
- PostgreSQL as durable source of truth
- PostgreSQL commit before Redis Pub/Sub publication
- WebSocket fan-out through FastAPI
- WebSocket reconnect/backfill from PostgreSQL
- JWT + RBAC + Argon2
- Docker + Docker Compose
- structured JSON logging + Prometheus + Grafana
- five logical detector modules
- raw vs derived separation
- Zeek 6+ target
- pinned tested Zeek tag/version
- explicit JA3/JA4 package handling
- JA3 + SSLBL as encrypted-malware MVP signal
- JA4/JA4S supplementary
- tcpreplay primary demo
- `zeek -r` development/debug
- no detector-per-microservice requirement
- Canonical Event Schema logical structure (envelope + typed `connection`/`dns`/`tls` payloads) — see `CANONICAL_EVENT_SCHEMA.md`; locked enough to implement after final source validation

## CONDITIONAL / NOT YET FINALIZED

- TimescaleDB
- exact UDP amplification/asymmetry feature formulation
- exact interpretation of the actual demo PCAP vantage point
- exact Zeek package versions/tags after team validation
- exact Redpanda topic names/topology
- NetFlow/IPFIX `connection_id` synthesis method (within Canonical Event Schema — blocked on actual exporter/format)
- NetFlow/IPFIX directional field mapping semantics (within Canonical Event Schema — blocked on confirmed exporter direction semantics, e.g. `flowDirection`)
- Feature/Window Schema
- detector input/output contracts
- Alert Schema
- PostgreSQL table schema
- WebSocket cursor format
- exact FastAPI routes
- final model/algorithm choice per detector
- final feature window sizes
- final benchmark measurements
- whether live packet capture is demonstrated in addition to the primary replay path

---

# 31. Current Stack Snapshot

| Layer | Choice |
|---|---|
| Frontend | React + Vite + TypeScript |
| Backend | Python + FastAPI |
| Network Telemetry | Zeek + Python Ingest Normalizer |
| Streaming | Redpanda |
| AI/ML | Scikit-learn + XGBoost + River |
| Hot State | In-memory + Redis |
| Persistent Storage | PostgreSQL (+ TimescaleDB pending schema/retention analysis) |
| Real-time | WebSockets |
| Security | JWT + RBAC + Argon2 |
| Infrastructure | Docker + Docker Compose |
| Observability | Structured JSON Logging + Prometheus + Grafana |
| Demo Replay | tcpreplay → monitored interface → Zeek live |
| Dev/Debug Replay | `zeek -r` |

---

# 32. Design Chain From Here

Do **not** jump into implementation before the following contracts are defined.

```text
1. Canonical Event Schema
        ↓
2. Redpanda Topics
        ↓
3. Feature / Window Schema
        ↓
4. Detector Inputs / Outputs
        ↓
5. Alert Schema
        ↓
6. PostgreSQL Schema
        ↓
7. FastAPI API Contract
        ↓
8. Alert publication + WebSocket reconnect/backfill implementation details
```

---

# 33. Canonical Event Schema — STATUS: COMPLETE (baseline)

> The task originally described in this section has been completed. The final logical schema (envelope + typed `connection`/`dns`/`tls` payloads) lives in `CANONICAL_EVENT_SCHEMA.md`. It is locked enough to implement after final source validation; three items remain conditional within it — NetFlow/IPFIX `connection_id` synthesis, NetFlow/IPFIX directional field mapping, and UDP amplification formulation — none of which block moving to the next design step (§33a).
>
> The original task description is kept below for historical record of the process that was followed.

The task was:

> **Design the Canonical Event Schema field matrix.**

The matrix should cover:

```text
Zeek conn.log
Zeek dns.log
Zeek ssl.log / TLS metadata
JA3 / JA4 fields
NetFlow
IPFIX
```

For every candidate field, determine:

```text
field name
meaning
data type
required / optional
raw / derived
source availability
detector(s) that need it
```

The process should be:

```text
Telemetry sources
      ↓
available raw fields
      ↓
threat requirements
      ↓
remove unnecessary fields
      ↓
common fields
      ↓
event-specific fields
      ↓
Canonical Event Schema
```

Only after the matrix is reviewed should the canonical event contract be implemented in Python/Pydantic.

Per checkpoint §32, do not jump into Pydantic implementation before the remaining contracts in the design chain (Redpanda Topics onward) are also defined.

---

# 33a. Immediate Next Task — Redpanda Topics

> **STATUS: IN PROGRESS — PARTITION KEY LOCKED**
>
> The raw canonical-event Redpanda partition key is now locked to `hash(src_ip)` for `connection`, `dns`, and `tls` topics. See `docs/architecture/REDPANDA_TOPICS_DRAFT_v4.md` §4 and `docs/backend/BACKEND_DECISIONS.md` BD-009.
>
> This is a scoped project-level decision. Partition counts and the remaining Redpanda topic/retention/error-handling decisions remain open and the Redpanda design document remains DRAFT.
>
> The next major design task remains Feature / Window Schema after the remaining Redpanda items are reviewed.

The original task is:

> **Define the Redpanda topic layout.**

For each topic, determine:

```text
topic name
event type(s) carried
publisher(s)
consumer(s)
partition key strategy
retention policy
error / dead-letter handling
```

This continues directly from the Canonical Event Schema (`CANONICAL_EVENT_SCHEMA.md`): topics carry canonical events (or, later, feature/window records) between pipeline stages, so the topic design should map cleanly onto the `event_type` discriminator (`connection` / `dns` / `tls`) already defined.

Only after Redpanda Topics are reviewed should work proceed to Feature/Window Schema per the §32 design chain.

---

# 34. Recovery Instruction

If future context is lost:

1. Read this file first.
2. Treat **LOCKED** decisions as already agreed.
3. Treat **CONDITIONAL / NOT YET FINALIZED** items as open.
4. Read `CANONICAL_EVENT_SCHEMA.md` — the Canonical Event Schema task (§33) is complete at baseline level.
5. Read the §33a status block — the raw-topic partition key (`src_ip`) is already **LOCKED**. Do not restart that decision. Review the remaining OPEN items in `docs/architecture/REDPANDA_TOPICS_DRAFT_v4.md` before proceeding to Feature / Window Schema.
6. Do not redesign the architecture, or the Canonical Event Schema's locked envelope/payload structure, from scratch unless a verified new requirement or benchmark requires it.
