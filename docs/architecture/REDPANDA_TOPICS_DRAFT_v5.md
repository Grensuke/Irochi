# SIH26145 — REDPANDA TOPIC DESIGN (DRAFT v5)

> **Status:** DRAFT — one item below is LOCKED; the document as a whole remains DRAFT pending project-lead / team review of the remaining OPEN items before promotion to `_FINAL`.
>
> **Continues from:** `docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md` and the architecture checkpoint's §33a ("Immediate Next Task — Redpanda Topics").
>
> **Scope:** This document defines the **raw canonical-event topics** between the Ingest Normalizer and Feature Processing. It intentionally does **not** finalize Feature/Window topics, Detector I/O topics, or Alert topics. Those remain subsequent steps in the design chain.

### Changelog

```text
v2 → v3
- Fixed duplicate "§12" heading (Redis Dependency Boundary / Relationship
  Between Redpanda and Other Components now §12 / §13, sequential).
- Fixed duplicate "§17" heading (Open Design Items / Review Checklist now
  §17 / §18, sequential).
- Deduplicated repeated bullets in §17 Open Design Items (Feature/Window
  state-management, Redis failure/availability behavior each now appear
  once).
- Straightened the malformed Redpanda fan-out diagram in §13.
- Corrected version label (title + Final Status) from v2 to v3.
- Added `retention.bytes` size cap alongside the 24h time-based limit in
  §6 (Redpanda/Kafka "whichever limit is reached first" semantics); exact
  byte value left OPEN pending event-size/throughput measurement, and
  tracked in §17 Open Design Items and §19 Decision Status Summary.

v3 → v4
- Raw-topic partition KEY locked to uniform `src_ip` (§4), on the basis
  of the aggregation-entity analysis in `FEATURE_WINDOW_SCHEMA_DRAFT_v3.md`
  §7: destination-centric (DDoS) and pair-centric (beaconing) correctness
  already depend on Redis under either candidate, and no currently-mapped
  TLS feature benefits from TLS-topic pair locality. Partition KEY is
  therefore locked independently of partition COUNT, which remains OPEN
  and benchmark-driven (§5) — this is a deliberate, scoped partial lock,
  not a promotion of the whole document to FINAL.
- Candidate B (`hash(src_ip, dst_ip)` for `tls`) is retained in §4 as a
  documented, not-selected alternative rather than removed, per team
  agreement to preserve the reasoning without leaving it as an active
  competing design.
- §19 Decision Status Summary updated to reflect the above; all other
  rows unchanged.

v4 → v5
- Replaced FEATURE_WINDOW_SCHEMA_DRAFT_v3.md §7 citations (§4 ×2, §17,
  §19) with FEATURE_WINDOW_SCHEMA_DRAFT_v4.md §7, and added BD-009
  (docs/backend/BACKEND_DECISIONS.md) as the stable decision record
  for the partition-key lock. No content or status change — citation/
  provenance fix only, closing the loop with FEATURE_WINDOW_SCHEMA_DRAFT_v5.md
  and BACKEND_DECISIONS.md BD-009.
```

---

## 1. Design Inputs and Guardrails

The Redpanda design must remain consistent with the approved architecture and Canonical Event Schema.

The current Canonical Event Schema uses:

```text
event_type ∈ {
  connection,
  dns,
  tls
}
```

and includes a schema version in the canonical event envelope.

The architecture requires the Redpanda design to define, for each topic:

```text
topic name
event type(s) carried
publisher(s)
consumer(s)
partition key strategy
retention policy
error / dead-letter handling
```

### Locked architectural boundaries respected by this draft

- Redpanda is the internal event-stream transport.
- Redis is not a mandatory transport stage for every event.
- Redis remains separate hot/shared state and live alert fan-out.
- PostgreSQL remains the durable alert source of truth.
- Five detector modules are logical modules, not five required microservices.
- NetFlow/IPFIX goes directly to the Ingest Normalizer rather than through Zeek.
- Canonical events contain observed/normalized facts.
- Derived/windowed values belong to the Feature/Window Schema.
- No throughput capability is claimed without benchmarking.
- The prototype is laptop-scale and should avoid unnecessary infrastructure.

Candidate throughput figures, if used for sizing, are **planning inputs only** and are not locked requirements or demonstrated capabilities.

---

## 2. Topic Layout

### 2.1 Proposed main topics

Use one raw canonical-event topic per canonical `event_type`:

| Topic | Event type carried | Publisher | Consumer | Initial partition proposal |
|---|---|---|---|---:|
| `irochi.events.connection.v1` | `connection` | Ingest Normalizer | Feature Processing | 6 |
| `irochi.events.dns.v1` | `dns` | Ingest Normalizer | Feature Processing | 3 |
| `irochi.events.tls.v1` | `tls` | Ingest Normalizer | Feature Processing | 3 |

### Why separate topics by event type?

This keeps the Redpanda topology aligned with the canonical `event_type` discriminator and prevents consumers from processing a single mixed stream when they only need one event type.

For example:

```text
DNS/DGA/Tunneling feature processing
        ↓
irochi.events.dns.v1

TLS/C2 feature processing
        ↓
irochi.events.tls.v1
```

The three topics still converge into the same logical Feature Processing stage.

### Status

The topic layout above is **PROPOSED**, not locked.

Feature/Window design may reveal a better partitioning or topic structure. Any material change must be reviewed before implementation.

---

## 3. Topic Naming Convention

Proposed naming convention:

```text
irochi.events.<event_type>.v<schema_major>
```

Examples:

```text
irochi.events.connection.v1
irochi.events.dns.v1
irochi.events.tls.v1
```

The major-version suffix allows an incompatible schema migration to run on a new topic without silently breaking existing consumers.

This complements the canonical event's `schema_version` field.

### Status

**PROPOSED.**

---

## 4. Partition Key Strategy

**Partition KEY: LOCKED.** Partition COUNT remains OPEN and benchmark-driven — see §5. These are separate decisions; locking the key does not lock the count.

### Candidate A — `src_ip` for all raw event topics — **LOCKED**

**Stable decision record:** `docs/backend/BACKEND_DECISIONS.md` BD-009. This
document contains the transport-specific implementation/design detail,
while BD-009 is the stable backend decision record.

```text
connection → hash(src_ip)
dns        → hash(src_ip)
tls        → hash(src_ip)
```

Advantages:

- source-centric locality;
- useful for source-based reconnaissance, DNS/DGA, and exfiltration aggregation;
- repeated TLS activity from one source remains relatively localized;
- one simple strategy across all raw event topics.

Risk (accepted, not blocking):

- high-volume sources can create partition skew;
- a source may communicate with many unrelated destinations;
- `src_ip` provides **partition locality, not event correlation**.

### Why this was selected over Candidate B

Resolved by the aggregation-entity analysis in `FEATURE_WINDOW_SCHEMA_DRAFT_v7.md` §7 and recorded as the stable project decision in `docs/backend/BACKEND_DECISIONS.md` BD-009:

- **Destination-centric work (DDoS) gets no locality benefit from either candidate.** A flood is defined by many different source IPs; this aggregation depends on Redis-backed destination-keyed state regardless of which raw-topic key is chosen (§12/§13 below).
- **Pair-centric work (C2 beaconing) gets no meaningful benefit from Candidate B either**, because its primary channel is `connection` (checkpoint §12.2: *"a general flow/timing signal, not a TLS-only signal"*), which both candidates key by plain `src_ip`. Candidate B's hybrid key would only have helped the narrower TLS-specific slice of beaconing evidence.
- **No currently-mapped TLS feature needs TLS-topic pair locality at all.** `ja3_blacklist_match` is per-event enrichment; the `connection`↔`tls` join is `connection_id`-keyed correlation state, independent of raw-topic partitioning either way.
- Net effect: correctness for destination- and pair-entity aggregation already depends on Redis under either candidate, so Candidate B offered a real operational cost (two key strategies to reason about, plus concentrating a single beaconing relationship's low-volume-but-regular traffic onto one partition) for zero identified feature-level benefit.

### Candidate B — hybrid source / relationship locality — **NOT SELECTED**

```text
connection → hash(src_ip)
dns        → hash(src_ip)
tls        → hash(src_ip, dst_ip)
```

Retained here deliberately, not deleted, so the reasoning stays visible without remaining an active competing design.

Original rationale (why this was considered): TLS/C2 beaconing is based on repeated connections between a source and destination over time. A compound `(src_ip, dst_ip)` key can keep a beacon relationship localized even though each connection has a different `connection_id`. This held up as sound reasoning for the general beaconing problem — it just doesn't apply to the `tls` topic specifically, since the primary beaconing signal lives on `connection`, not `tls` (see above).

**Future optimization:** may be reconsidered only if a future TLS-specific feature or benchmark finding demonstrates a real benefit to TLS-topic pair locality. Not a live alternative in the current design.

### Why not simply use `connection_id` for TLS?

`connection_id` identifies an individual flow/session. Repeated beaconing connections are separate flows and therefore normally receive different connection identifiers.

Using `connection_id` as the TLS partition key could scatter the repeated connections that the beacon detector needs to analyze together.

Also, `connection_id` does not itself correlate an arbitrary DNS query with a later unrelated TLS connection.

### Important distinction

`connection_id` remains useful for **event-level correlation where the identifier is actually shared**, but partition locality should be designed around the downstream aggregation problem.

### Decision — RESOLVED

The Feature/Window Schema (`FEATURE_WINDOW_SCHEMA_DRAFT_v7.md` §7) evaluated source-centric, destination-centric, pair, and connection-level correlation needs against the actual detector-to-feature mapping, and BD-009 records the resulting project-level lock. Candidate A is locked; Candidate B is preserved above as a documented, not-selected alternative.

---

## 5. Partition Counts

Initial laptop-scale proposal:

```text
connection = 6
dns        = 3
tls        = 3
```

Rationale:

- connection events are expected to be the highest-volume canonical event class;
- DNS and TLS are typically lower-volume relative to connection telemetry;
- the proposal leaves room for several Feature Processing partitions on a demo machine.

### Important

These counts are **NOT locked**.

Final sizing depends on:

- actual demo hardware;
- number of Feature Processing workers;
- replay rate;
- observed events/sec;
- consumer lag;
- CPU and memory;
- partition skew.

The architecture explicitly requires actual throughput to be benchmarked rather than claimed.

---

## 6. Retention Policy

Proposed raw-event retention:

| Topic | Cleanup policy | Time-based limit | Size-based limit (`retention.bytes`) | Reason |
|---|---|---:|---:|---|
| `irochi.events.connection.v1` | `delete` | 24 hours | TBD | replay/debug buffer and consumer recovery |
| `irochi.events.dns.v1` | `delete` | 24 hours | TBD | replay/debug buffer and consumer recovery |
| `irochi.events.tls.v1` | `delete` | 24 hours | TBD | replay/debug buffer and consumer recovery |

Redpanda is treated as a **bounded transport/replay buffer**, not the long-term source of truth for alerts.

### Why both a time limit and a size limit?

A time-only retention policy (`retention.ms`) does not bound disk usage on its own. If actual event volume during the demo/replay is higher than assumed, a purely time-based policy can let a topic grow unexpectedly large within the 24-hour window, which matters on laptop-scale storage.

Therefore each raw-event topic should carry **both**:

```text
retention.ms    = 24h (86400000)
retention.bytes = <TBD, per-partition cap>
```

with Redpanda/Kafka-standard semantics: **whichever limit is reached first triggers cleanup** for that partition.

### Do not invent the byte number yet

`retention.bytes` should **not** be set to an arbitrary placeholder value in this document. It must be derived from:

```text
approximate canonical-event size (JSON, post-compression if enabled)
        ×
expected/observed events-per-second for that topic
        ×
desired retention window
        ÷
partition count for that topic
```

This depends on the same benchmark-driven inputs (`§5 Partition Counts`, `§16.1 Producer compression`) that are already flagged as pending measurement. Until then, `retention.bytes` remains `TBD` per topic/partition rather than a guessed number.

### Why `delete` instead of `compact`?

These topics represent event streams containing many observations. They are not a latest-state-per-key changelog.

Therefore:

```text
cleanup.policy = delete
```

is the current proposal.

### Status

24-hour retention and `delete` cleanup are **PROPOSED**.

A `retention.bytes` size cap alongside the 24-hour time limit is **PROPOSED**; the exact byte value is **OPEN**, pending event-size and throughput measurement.

Retention should be revisited after volume/throughput measurements and storage analysis.

---

## 7. Dead-Letter Handling

### Proposed DLQ

Use one shared raw-event DLQ for the MVP:

```text
irochi.events.dlq.v1
```

This keeps the laptop-scale deployment operationally simple.

The DLQ is a **safety net**, not the primary validation mechanism.

### Producer-side validation

The Ingest Normalizer should validate canonical events before publishing.

Therefore:

```text
Telemetry
   ↓
Normalizer validation
   ↓
valid?
  ├── NO  → failure handling / DLQ
  └── YES → Redpanda
```

### DLQ metadata

A DLQ record should preserve enough information to reconstruct the failure context, including:

```text
original topic
partition
offset
failure reason
failure stage
schema/version information where available
original/raw payload
```

Headers are preferred for transport metadata when practical.

### Consumer failures

A malformed or otherwise poison record must not indefinitely stall the affected consumer.

The failure path should:

```text
detect failure
    ↓
capture failure context
    ↓
publish/copy to DLQ
    ↓
advance past the poison record according to the consumer strategy
```

The exact retry/backoff and replay mechanism is a later implementation detail and should be finalized with operational requirements.

### Status

The shared-DLQ choice is **PROPOSED**.

Per-topic DLQs remain a valid alternative if later operational analysis shows clearer ownership or isolation is worth the additional topics.

---

## 8. Consumer Group Topology

The proposed raw-event consumer group is:

```text
irochi-feature-processing
```

It subscribes to:

```text
irochi.events.connection.v1
irochi.events.dns.v1
irochi.events.tls.v1
```

### Why one consumer group?

Feature Processing is a logical pipeline stage.

Multiple Feature Processing instances may scale horizontally through Redpanda partitions, while keeping the stage conceptually unified.

The detector modules do **not** directly consume the raw event topics in this design.

Instead:

```text
Raw Canonical Events
        ↓
Feature Processing
        ↓
Feature / Window records
        ↓
Detector modules
```

Feature/Window topics are intentionally left for the next design step.

---

## 9. Delivery Semantics

### Proposed delivery model

```text
At-least-once
```

This is a deliberate choice for a security-detection pipeline where losing an event can be worse than processing an event more than once.

### Producer idempotence

Enable producer idempotence for the Ingest Normalizer where supported by the chosen client configuration.

This helps avoid duplicate **publishes caused by producer retries**.

### Consumer duplicate tolerance

Producer idempotence does **not** eliminate all downstream redelivery.

Consumers must still tolerate duplicate delivery caused by retries, rebalances, crashes, or replay.

Therefore:

```text
producer idempotence
≠
consumer exactly-once processing
```

The exact deduplication/idempotency strategy belongs to Feature/Window and downstream processing design.

---

## 10. Ordering

Redpanda ordering is guaranteed **within a partition**, not globally across a topic.

This draft therefore does not require global ordering.

The intended requirement is:

```text
related records that need local processing locality
→ same partition where the selected key provides that locality
```

The exact ordering assumptions for feature windows will be finalized alongside the Feature/Window Schema.

Do not assume that timestamps alone imply delivery order across partitions.

Feature/Window processing should distinguish **event time** from
**processing/delivery time** when building windows or detecting
out-of-order records. The exact watermark/late-event policy is deferred
to the Feature/Window design.

---

## 11. Serialization

### MVP proposal

Use:

```text
JSON
```

for the laptop-scale demo.

Reasons:

- simple to inspect;
- easy to debug;
- easy to integrate with Python;
- low operational overhead for the prototype.

Future alternatives:

```text
Avro
Protobuf
```

may be evaluated if measured throughput, payload size, compatibility requirements, or schema-governance needs justify them.

A schema registry is intentionally out of scope for the current MVP.

### Status

**PROPOSED**, not locked.

---

## 12. Redis Dependency Boundary

Redpanda partitioning is a **transport/load-distribution decision**.
Feature/Window aggregation is a **processing-state decision**.

Where cross-worker or cross-partition state is required, Redis may be used
as shared hot state. This draft does not lock the exact Redis dependency,
aggregation mechanism, or failure-handling strategy.

If event-id-based deduplication is used downstream, the implementation
must not mark an event as processed before its corresponding state update
is safely committed.

The Feature/Window design should explicitly evaluate:

```text
atomic state-update + deduplication
idempotent state updates
Redis failure behavior
deduplication TTL
replay/redelivery behavior
```

Redis availability and latency should be benchmarked deliberately if
detection correctness depends on Redis-backed state.

### DDoS-specific partitioning consideration

Volumetric DDoS is fundamentally destination-centric.

With source-based partitioning, a distributed flood from many source IPs
can be spread across multiple Redpanda partitions, so no single Feature
Processing worker necessarily sees the complete victim-level signal.

A single high-rate source also remains concentrated on one partition and
may create a hot partition during the burst.

Therefore, Redpanda partitioning must **not** be treated as the correctness
mechanism for DDoS aggregation. Feature/Window processing may require
shared destination-centric state, potentially backed by Redis, to combine
evidence across partitions.

This is a downstream aggregation decision, not a reason to force the
Redpanda key to a destination key in this draft.

### Status

**PROPOSED / OPEN.**

## 13. Relationship Between Redpanda and Other Components

The raw-event path is:

```text
Zeek -------------------+
                         |
NetFlow/IPFIX -----------+--> Ingest Normalizer
                                 |
                                 v
                            Redpanda
                         /       |       \
                        v        v        v
                 connection    dns       tls
                    topic      topic    topic
                         \       |       /
                          \      |      /
                           v     v     v
                         Feature Processing
```

Important boundaries:

```text
React ─X→ Redpanda
React ─X→ PostgreSQL
React ─X→ Redis
```

The frontend reaches backend data through FastAPI/approved WebSocket interfaces.

Redpanda is an internal backend transport.

### Cross-topic `connection_id` correlation

Topic separation and partition locality do not guarantee co-location of
records that share the same `connection_id`.

For example, a `connection` record and a corresponding `tls` record may
share `connection_id` while residing in different topics and potentially
different partitions.

Feature Processing must therefore not assume that equal `connection_id`
values imply same-worker delivery. Cross-topic correlation may require
short-lived shared state or another downstream correlation mechanism.

The exact correlation mechanism is intentionally deferred to the
Feature/Window design.

---

## 14. What Redpanda Does NOT Do

Redpanda is not:

- the durable alert source of truth;
- the frontend data-access layer;
- the replacement for Redis hot state;
- the replacement for PostgreSQL;
- the detector itself;
- the Feature/Window Schema;
- a reason to create one topic per detector;
- a reason to create one microservice per threat class.

The architecture remains:

```text
Redpanda
= move backend records between pipeline stages
```

---

## 15. Proposed Raw Topic Flow

Current proposal:

```text
                      Ingest Normalizer
                             |
             +---------------+---------------+
             |               |               |
             v               v               v
     connection.v1       dns.v1          tls.v1
             |               |               |
             +---------------+---------------+
                             |
                             v
                    Feature Processing
                             |
                             v
                    Feature / Window
                      (next design)
```

Errors:

```text
Invalid / poison raw event
             |
             v
   irochi.events.dlq.v1
```

---

## 16. Additional Operational Considerations

### 16.1 Producer compression

Producer-side compression is a **PROPOSED** optimization.

Candidate algorithms:

```text
lz4
zstd
```

Compression can reduce network and broker storage pressure, especially
for the high-volume `connection` topic carrying JSON records.

The final algorithm should be chosen using actual CPU, throughput,
payload-size, and latency measurements on the demo environment.

Do not treat compression as a benchmark result until measured.

### 16.2 Raw-event forensic and retraining retention gap

The current proposal treats Redpanda as a bounded replay/transport buffer.
With 24-hour retention, raw canonical events may expire after that period.

If PostgreSQL stores alerts rather than all raw canonical events, then
expired non-alerting telemetry may no longer be available for:

- historical forensic investigation;
- reconstructing past host behavior;
- building future training/retraining datasets.

This is acceptable as an MVP trade-off unless the SIH requirements demand
long-term raw-event retention, but it must remain explicit.

Long-term raw/feature retention is therefore **OUT OF SCOPE / OPEN** and
requires separate storage, cost, and retention analysis.

### 16.3 Redpanda internal security

For the single-host Docker-based MVP, Redpanda authentication/authorization
and service-to-service transport encryption are deferred.

For a production or multi-host deployment, Redpanda security should be
evaluated explicitly, including:

- client authentication;
- topic-level authorization/ACLs;
- encrypted transport where required.

This is a conscious deferral, not a claim that internal broker security
is unnecessary in production.

---

## 17. Open Design Items

The following remain explicitly **PROPOSED / OPEN**:

- [x] ~~Final partition-key strategy~~ — **LOCKED** (§4): uniform `src_ip`, recorded in `BD-009`, with supporting analysis in `FEATURE_WINDOW_SCHEMA_DRAFT_v7.md` §7
- [ ] Final partition counts (§5) — still OPEN, benchmark-driven
- [ ] Final retention duration
- [ ] `retention.bytes` size cap per topic/partition (pending event-size/throughput measurement)
- [ ] Shared DLQ vs per-topic DLQs
- [ ] Exact retry/backoff/replay behavior
- [ ] JSON vs Avro/Protobuf
- [ ] Whether a schema registry is ever justified
- [ ] Final deployment replication strategy
- [ ] Final Feature/Window state-management and deduplication semantics
- [ ] Redis failure/availability behavior where shared state is required
- [ ] Benchmark-driven sizing
- [ ] Compression algorithm after benchmark comparison
- [ ] Long-term raw/feature retention strategy for forensics and retraining

### Explicitly NOT being decided here

- Feature/Window topic design
- Feature/Window partitioning
- Detector input/output contracts
- Alert topic semantics
- Alert Schema
- PostgreSQL schema
- Final FastAPI routes
- WebSocket cursor format
- Final ML/detector implementation

Those follow later in the architecture design chain.

---

## 18. Review Checklist

Before promoting this document from DRAFT to FINAL, verify:

### Topic structure

- [ ] Three canonical event topics map cleanly to `connection`, `dns`, `tls`.
- [ ] Topic naming is consistent.
- [ ] No unnecessary detector-specific raw topics exist.

### Partitioning

- [x] Locked partition key is supported by the Feature/Window aggregation analysis.
- [ ] Source skew is considered.
- [ ] Beaconing locality is considered.
- [ ] `connection_id` is not incorrectly treated as a campaign-level partition key.

### Reliability

- [ ] At-least-once semantics are acceptable.
- [ ] Producer idempotence is enabled/validated.
- [ ] Consumers tolerate redelivery.
- [ ] Poison records cannot permanently stall a partition.
- [ ] DLQ metadata is sufficient for troubleshooting.

### Storage

- [ ] Retention is validated against demo storage requirements.
- [ ] Redpanda remains a bounded transport/replay layer.
- [ ] PostgreSQL remains durable alert storage.

### Performance

- [ ] Partition counts are validated using the actual demo environment.
- [ ] Throughput and lag are measured rather than assumed.

### Compatibility

- [ ] Topics carry records compatible with the Canonical Event Schema.
- [ ] Schema versioning is clear.
- [ ] No raw/derived boundary is violated.

---

## 19. Decision Status Summary

| Design Item | Status |
|---|---|
| 3 raw topics by canonical event type | **PROPOSED** |
| Topic naming convention | **PROPOSED** |
| `src_ip` partitioning (raw-topic partition KEY) | **LOCKED** — recorded in `BD-009`, with supporting analysis in `FEATURE_WINDOW_SCHEMA_DRAFT_v7.md` §7 |
| Candidate B — `(src_ip, dst_ip)` for `tls` | **NOT SELECTED** — future benchmark/feature-driven optimization only |
| 6/3/3 partitions | **PROPOSED** |
| 24-hour retention | **PROPOSED** |
| `retention.bytes` size cap (value) | **PROPOSED / OPEN** |
| `delete` cleanup | **PROPOSED** |
| Shared DLQ | **PROPOSED** |
| At-least-once delivery | **PROPOSED** |
| Producer idempotence | **PROPOSED** |
| Consumer duplicate tolerance | **PROPOSED** |
| JSON | **PROPOSED** |
| `irochi-feature-processing` group | **PROPOSED** |
| Producer compression (`lz4` / `zstd`) | **PROPOSED** |
| Event-id-based downstream deduplication | **PROPOSED / OPEN** |
| Redis dependency for cross-partition/shared state | **PROPOSED / OPEN** |
| Long-term raw/feature retention | **OUT OF SCOPE / OPEN** |
| Redpanda internal auth/encryption | **DEFERRED** |

Except where explicitly marked LOCKED, items in this table remain subject to project-lead/team approval.

---

## 20. Next Design Step

Once this raw-topic design is reviewed and approved:

```text
Redpanda Topics
        ↓
Feature / Window Schema
        ↓
Detector Inputs / Outputs
        ↓
Alert Schema
        ↓
PostgreSQL Schema
        ↓
FastAPI API Contract
```

The **Feature / Window Schema** should use the Redpanda design above as an input, especially when deciding:

- aggregation keys;
- window ownership;
- state locality;
- cross-partition requirements;
- detector-specific feature streams.

---

## 21. Design Principles Carried Forward

The following distinctions should remain explicit in later design work:

```text
Redpanda partition key
    ≠
Feature/Window aggregation key
    ≠
event correlation key
```

Partitioning primarily provides transport load distribution and
partition-local ordering.

Feature/Window processing defines the behavioral aggregation model.

Shared state such as Redis may provide cross-worker/cross-partition
state when locality alone is insufficient.

These are intentionally related decisions, but they must not be conflated.

---

## 22. Final Status

**DRAFT v5 — partition KEY (§4) is LOCKED and approved; all other items, including partition COUNT (§5), await project-lead/team review before this document is promoted to `_FINAL`.**

No Redpanda topics should be implemented in code from this document until the remaining OPEN items are explicitly reviewed and approved. The locked partition-key decision may be used as an approved architectural input by later implementation work, but no Redpanda topic creation or Ingest Normalizer implementation should begin until the remaining relevant design items have been reviewed and approved.
