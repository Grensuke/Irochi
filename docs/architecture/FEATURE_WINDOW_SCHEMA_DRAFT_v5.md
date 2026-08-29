# SIH26145 — FEATURE / WINDOW SCHEMA (DRAFT v5)

> **Status:** DRAFT — proposed, not yet locked. Requires project-lead / team review before promotion to `_FINAL`.
>
> **Continues from:** `docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md`, `docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md` (§9, §10, §12, §14, §15), and `REDPANDA_TOPICS_DRAFT.md`.
>
> **Scope:** This document defines what a **feature/window record** is, how derived signals are computed and keyed, and how derived-state processing relates to the approved Redpanda design. It does **not** finalize Detector I/O contracts, Alert Schema, or PostgreSQL schema — those remain later steps.

### v4 → v5 revision summary

- Resolved partition-key decision provenance by using `BD-009` as the stable decision record and `REDPANDA_TOPICS_DRAFT_v4.md` §4 as the design location.
- Removed duplicate DDoS hot-key and pair-state items from §21 and corrected their section references to §16.1 / §16.2.
- Updated the partition-key status language from pending/recommendation wording to inherited LOCKED wording.
- Fixed the extra blank-line gap in §3.

### v3 → v4 revision summary

- Raw-topic partition key is now treated as an approved inherited decision recorded in `docs/backend/BACKEND_DECISIONS.md` BD-009 and reflected in `REDPANDA_TOPICS_DRAFT_v4.md`: uniform `src_ip`.
- Reconciled Redis state shapes: sliding windows use time buckets, tumbling windows use window-instance keys, and session/correlation state uses correlation-specific keys.
- Made Tier 1 pair tracking explicitly internal gating state only; Tier 2 is the feature-producing state.
- Preserved the directional `(src_ip, dst_ip)` pair-key rule and the remaining PROPOSED / OPEN scope.

---

## 1. Design Inputs and Guardrails

This design must remain consistent with decisions already made upstream.

### Locked/decided boundaries respected by this draft

- Canonical events are observed/normalized facts only; derived/windowed values belong here (`CANONICAL_EVENT_SCHEMA_FINAL.md` §2).
- Five detector modules are logical modules, not five required microservices (architecture checkpoint §11).
- In-memory state is for ultra-hot per-worker calculations; Redis is for shared/cross-worker state (architecture checkpoint §10).
- Exact window lengths were explicitly left unfinalized (architecture checkpoint §9) — this draft does not invent them.
- `amplification_ratio` was explicitly deferred pending demo-PCAP review (architecture checkpoint §12.1) — this draft does not resolve it either.
- `REDPANDA_TOPICS_DRAFT_v5.md` §4 deferred the raw-topic partition key to this document, specifically asking it to evaluate source-centric, destination-centric, pair, and connection-level correlation needs.
- `REDPANDA_TOPICS_DRAFT_v5.md` §12/§13 already flagged that DDoS aggregation and cross-topic `connection_id` correlation cannot rely on Redpanda partition locality alone.
- No throughput, latency, or window-stability claim is made without benchmarking.

---

## 2. Three Derived-Signal Mechanisms

Not all "features" are windowed aggregates. Conflating them produces a schema that is either too heavy for simple cases or too thin for stateful ones. This draft distinguishes three mechanisms:

| Mechanism | What it is | Needs a window? | Needs entity state? | Examples |
|---|---|---|---|---|
| **Enrichment** | Computed from a single event's own fields, or looked up against static/external reference data | No | No | `domain_entropy`, `query_length`, `n_gram_score`, label-length statistics, `ja3_blacklist_match` |
| **Windowed aggregation** | Computed by accumulating multiple events for the same entity over a time window | Yes | Yes | `packet_rate`, `byte_rate`, `syn_ratio`, `unique_destination_ports`, `query_frequency`, `beacon_periodicity`, `outbound_inbound_ratio` |
| **Connection-level correlation** | Joins records that share a `connection_id` across different raw topics | No (join, not accumulation) | Yes (short-lived, per `connection_id`) | Attaching TLS fingerprint outcome (e.g. `ja3_blacklist_match`) to the same flow's `connection` byte/packet counts |

### Why this distinction matters for the schema

An enrichment feature can be computed the moment a single canonical event arrives and carries no window fields at all. A windowed aggregate cannot exist until a window closes (or, for sliding windows, until it is next recomputed) and must carry an entity key plus a window range. A connection-level correlation is neither — it is waiting for a *second event with a matching key*, not for time to pass or for volume to accumulate. Treating all three as one undifferentiated "Feature record" either forces empty window fields onto enrichment records or forces a fake window onto a join. Section 5 defines a shared envelope with an explicit `mechanism` field so each case only carries the fields it actually needs.

### Status

**PROPOSED.** This typology, not the specific feature list, is the load-bearing decision here.

---

## 3. Aggregation Entity Types

For the **Pair** entity, the key is directional:

```text
(src_ip, dst_ip) ≠ (dst_ip, src_ip)
```

The pair must not be sorted or otherwise canonicalized because C2
beaconing represents a directional source→destination relationship.

For the mechanisms that do need state (windowed aggregation, correlation), the entity being tracked is not the same across detectors:

| Entity type | Key | What it tracks |
|---|---|---|
| **Source** | `src_ip` | Behaviour of one host as an originator, regardless of who it talks to |
| **Destination** | `dst_ip` | Behaviour observed *at* one host as a target, regardless of who is talking to it |
| **Pair** | `(src_ip, dst_ip)` | A specific relationship between two hosts over time |
| **Connection** | `connection_id` | Facts belonging to one specific flow, joined across the topics that observed it |

This is the same typology `REDPANDA_TOPICS_DRAFT_v5.md` §4 asked this document to resolve. §7 below uses it to close that decision gate.

---

## 4. Detector-to-Entity-and-Mechanism Mapping

Grounded directly in architecture checkpoint §12, §14, §15:

| Detector domain | Feature | Mechanism | Entity | Primary raw topic(s) |
|---|---|---|---|---|
| DDoS | `packet_rate`, `byte_rate`, `syn_ratio` | Windowed | **Destination** | `connection` |
| DDoS | `source_ip_entropy` | Windowed | **Destination** (diversity of sources hitting this victim — a destination-keyed measurement despite the name) | `connection` |
| DDoS | UDP amplification/asymmetry metrics | Windowed | **OPEN** — tied to the same undecided capture-point question as `amplification_ratio` (§12.1); may be destination-keyed (victim) or source-keyed (reflector) depending on where the sensor sits | `connection` |
| Recon | `unique_destination_ports`, `unique_destination_hosts`, `connection_fan_out`, `scan_rate` | Windowed | **Source** | `connection` |
| DNS/DGA | `domain_entropy`, `query_length`, `n_gram_score`, label-length statistics | **Enrichment** | n/a (per-event) | `dns` |
| DNS/tunneling | `query_frequency`, record-type distribution | Windowed | **Source** | `dns` |
| TLS/C2 | `ja3_blacklist_match` | **Enrichment** | n/a (per-event lookup) | `tls` |
| TLS/C2 | Flow-level join (attach TLS outcome to its flow's byte/packet counts) | **Correlation** | **Connection** | `connection` + `tls` |
| C2 beaconing (general) | `inter_arrival_time`, `beacon_periodicity`, periodicity variance, regularity, connection frequency, repeated-destination behaviour | Windowed | **Pair** | `connection` (checkpoint §12.2: *"a general flow/timing signal, not a TLS-only signal"*) |
| Exfiltration | `outbound_inbound_ratio`, `byte_rate`, windowed transfer volume, large-transfer indicators | Windowed | **Source** | `connection` |

Two things worth flagging explicitly because they are easy to miss on a first read:

1. **C2 beaconing is pair-entity, and its primary channel is `connection`, not `tls`.** This matters for §7 below — a partition-key design that only gives pair locality to the `tls` topic does not actually help the primary beaconing signal.
2. **`source_ip_entropy` is a destination-entity feature.** It is easy to assume anything with "source" in the name is source-keyed. It isn't — it describes the diversity of sources converging on one destination, so it lives with the DDoS/destination row, not the source-entity rows.

### Status

**PROPOSED.** The mechanism/entity assignments follow directly from already-decided threat-to-signal reasoning; nothing here re-opens those decisions.

---

## 5. Feature Record Schema Shape

Mirroring the canonical event's envelope-plus-typed-payload pattern:

```text
FeatureRecord
├── Envelope
└── Typed Payload
    ├── DdosFeaturePayload
    ├── ReconFeaturePayload
    ├── DnsFeaturePayload        (carries both enrichment and windowed fields)
    ├── TlsC2FeaturePayload      (carries enrichment, correlation, and windowed fields)
    └── ExfilFeaturePayload
```

### Envelope fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `feature_id` | UUID/string | Yes | Unique identifier generated by Feature Processing |
| `mechanism` | enum | Yes | `enrichment`, `windowed`, or `correlation` (§2) |
| `detector_domain` | enum | Yes | `ddos`, `recon`, `dns`, `tls_c2`, or `exfil` |
| `entity_type` | enum | Conditional | `source`, `destination`, `pair`, or `connection`; omitted for `enrichment` records |
| `entity_key` | string | Conditional | The actual key value (`src_ip`, `dst_ip`, `"src_ip\|dst_ip"`, or `connection_id`); omitted for `enrichment` records |
| `window_type` | enum | Conditional | `tumbling`, `sliding`, or `session`; present only for `windowed` records |
| `window_start` / `window_end` | int64 | Conditional | Epoch microseconds; present only for `windowed` records |
| `computed_at` | int64 | Yes | Time Feature Processing emitted the record (epoch microseconds) — mirrors `ingest_timestamp`'s role: observability/lag measurement, not a detection feature |
| `schema_version` | string | Yes | Version of the feature-record contract |
| `provenance` | object | Optional | References/summary describing the raw events contributing to the record; exact shape remains open |

### Status

**PROPOSED.**

---

## 6. Proposed Processing Invariant: Feature Records Are Snapshots, Not Deltas

> **A feature record for a given `(entity_key, window_start, window_end)` (or a given `connection_id` correlation) should represent a complete, self-contained computed value at the moment of emission — never an incremental delta that must be added to a prior record.**

This follows from the inherited at-least-once delivery semantics and the need for detectors to receive stable calculated state. Rejecting this invariant would reopen the downstream delivery/idempotency design rather than merely changing a window size.

Duplicate delivery is therefore handled by retaining/replacing the self-contained snapshot rather than summing it with an earlier snapshot.

### Snapshot freshness / revision rule

For the same logical identity:

```text
(entity_key, window_start, window_end)
```

or:

```text
connection_id
```

a newer `revision` supersedes an older revision.

Older revisions must never overwrite newer state.

`computed_at` may support freshness comparison when worker clock ordering is trusted. If multiple workers can concurrently emit snapshots and clock skew can make wall-clock comparison unsafe, a Redis-native monotonic revision/sequence should be used as the definitive ordering mechanism.

---

## 7. Raw Redpanda Partition-Key Decision (Inherited)

`REDPANDA_TOPICS_DRAFT_v4.md` §4 and `docs/backend/BACKEND_DECISIONS.md` BD-009 now record Candidate A as locked:
`src_ip` for all three raw topics. The Feature/Window aggregation analysis
below is the evidence that informed that decision; it is no longer an open
gate.

**Locked partition key: Candidate A — `src_ip` for all three raw topics.**

Reasoning, using the §4 mapping:

- **Destination-entity work (DDoS) gets no partition-locality benefit from either candidate.** A flood is defined by many *different* source IPs; hashing by `src_ip` scatters attacking sources regardless of which candidate is chosen. This aggregation was always going to depend on Redis-backed destination-keyed state (already noted in `REDPANDA_TOPICS_DRAFT_v5.md` §12). Neither candidate changes that.
- **Pair-entity work (C2 beaconing) gets no meaningful benefit from Candidate B either, because its primary channel is `connection`, not `tls`.** Candidate B only hybrid-keys the `tls` topic. General flow-timing beaconing (checkpoint §12.2) is computed from `connection` events, which both candidates key by plain `src_ip`. So Candidate B's hybrid key would only help pair-locality for the narrower TLS-specific slice of beaconing evidence, while the primary signal path still needs Redis-backed pair state under *either* candidate.
- **Source-entity work (recon, DNS/DGA windowed features, exfiltration) is the only category that genuinely benefits from partition locality, and Candidate A serves it uniformly across all three topics.**
- **Hybrid keying adds a real operational cost for a narrow benefit.** A `(src_ip, dst_ip)` key on `tls` concentrates a single high-rate beaconing relationship — low volume but very regular, which is exactly what makes it detectable — onto one partition, plus it means two different key strategies have to be reasoned about instead of one.

Net effect: correctness for destination- and pair-entity aggregation already depends on Redis under either candidate, so the only real trade-off left is "one simple, uniform key" vs. "one uniform key plus one narrow, TLS-only optimization." Candidate A is the simpler choice that gives up nothing correctness-wise.

This decision is already approved and recorded as a scoped project-level lock
in `REDPANDA_TOPICS_DRAFT_v4.md` §4 and `docs/backend/BACKEND_DECISIONS.md` BD-009. If a future benchmark or
new TLS-specific feature shows a meaningful benefit from TLS-topic pair
locality, Candidate B may be reintroduced later as a targeted, measured
optimization. That would be a future decision, not an unresolved alternative
in the current design.

### Additional evidence against the TLS-specific hybrid key

The current feature mapping contains no TLS-topic feature that requires
pair-local aggregation.

- `ja3_blacklist_match` is per-event enrichment and does not require
  pair locality.
- `connection`↔`tls` correlation is keyed by `connection_id` and may
  require shared state regardless of TLS partition locality.
- General C2 beaconing is computed primarily from `connection` events,
  whose raw-topic key is `src_ip` under both Redpanda candidates.

Therefore Candidate B currently provides no identified feature-level
benefit over Candidate A. A future TLS-topic pair-local optimization
would require a newly justified feature or benchmark finding.

### Status

**LOCKED (inherited from Redpanda v4 §4 and recorded in BD-009).** The lock applies to the raw
partition key only; partition counts and other Redpanda choices remain open.

---

## 8. Window Model

### Window taxonomy

The Feature/Window layer supports three window mechanisms:

| Window type | Behaviour | Current use |
|---|---|---|
| Tumbling | Fixed, non-overlapping | Bounded snapshots/counts where interval-level aggregation is appropriate |
| Sliding | Continuously recomputed over a bounded rolling horizon | Time-sensitive rates, source/destination behaviour, and pair-timing features |
| Session | Closes after a gap of inactivity | Bounded activity/transfer sessions where session closure is semantically meaningful |

**Status:** **LOCKED (taxonomy only).** The three mechanism types are the
supported taxonomy. Exact feature-to-window assignments and all duration/
bucket/gap parameters remain PROPOSED / OPEN.

### Feature-level window mapping

Window mechanism is assigned at the **feature** level rather than forcing one
mechanism per detector domain.

| Detector / feature | Entity | Mechanism | Status / rationale |
|---|---|---|---|
| DDoS: `packet_rate`, `byte_rate`, `syn_ratio`, `source_ip_entropy` | Destination | **Sliding** | Time-sensitive victim-side burst/diversity signal |
| DDoS: UDP amplification/asymmetry metrics | **OPEN** | **OPEN** | Capture-point dependent; follows checkpoint §12.1 / `amplification_ratio` question |
| Recon: `unique_destination_ports`, `unique_destination_hosts`, `connection_fan_out` | Source | **Tumbling** | Bounded breadth measurement over an observation interval |
| Recon: `scan_rate` | Source | **Sliding** | Rate-sensitive scan behaviour |
| DNS/tunneling: `query_frequency` | Source | **Sliding** | Recent DNS request rate |
| DNS/tunneling: record-type distribution | Source | **Tumbling** | Distribution over a bounded observation interval |
| Beaconing: `inter_arrival_time`, `beacon_periodicity`, periodicity variance, regularity, connection frequency | Pair | **Sliding** | Bounded rolling timing signal; Tier 2 state may update incrementally |
| Beaconing: `repeated-destination behaviour` | Pair | **OPEN** | Mechanism still needs explicit selection |
| Exfiltration: `outbound_inbound_ratio`, `byte_rate` | Source | **Sliding** | Rolling transfer-rate/directionality signal |
| Exfiltration: `windowed transfer volume`, `large-transfer indicators` | Source | **Windowed** | Kept aligned with checkpoint terminology; exact semantics (per-connection vs session aggregate) remain OPEN pending confirmation |

### Pair-timing implementation note

For beaconing, **Sliding** is the mechanism. The implementation may maintain
the sliding calculation incrementally as new observations arrive rather than
recompute the entire raw-event set for every evaluation. "Incremental" or
"rolling state" is an implementation technique, not a fourth window type.

Beaconing is **not Session-primary**. A session inactivity threshold that is
too close to the interval being detected can fragment a regular beacon
sequence, so Session is not used as the primary periodicity mechanism here.

### Exfiltration scope note

The architecture checkpoint lists `windowed transfer volume` and
`large-transfer indicators` as derived signals but does not specify whether
they are properties of a single connection or aggregates across a bounded
transfer/session. This draft therefore keeps their current **Windowed /
Source** classification while making the semantic question explicit as OPEN.

### Deriving window length instead of guessing it

Consistent with architecture checkpoint §9 and the Redpanda design's refusal to
invent a `retention.bytes` number before measurement, this draft does not assign
specific durations. Each detector-domain window length should be derived from:

```text
time-to-signal budget
        vs.
statistical stability
```

evaluated against a representative dataset/PCAP once available.

For example, DDoS burst windows are expected to favour low latency, while
low-and-slow recon/beaconing behaviour may favour longer stability. These are
directional expectations only; the actual numbers remain OPEN.

### A risk worth naming now: long windows vs. the 24h raw-retention buffer

If any detector's eventual window approaches the 24-hour raw-retention horizon,
a Feature Processing worker that crashes cannot always reconstruct the full
window purely from Redpanda replay. Such entities may therefore need periodic
state checkpointing (for example, persisted in-progress Redis state) rather
than relying entirely on raw-event replay. This is an OPEN risk because the
actual window lengths are not yet finalized.

### Status

**PROPOSED (feature mapping). Durations, bucket widths, and session gaps remain
OPEN and benchmark/dataset-dependent.**

---
## 9. State Locality & Redis Strategy

Following `REDPANDA_TOPICS_DRAFT_v5.md` §12/§21's distinction — partition key is a transport/load decision, Redis is the correctness backstop when locality isn't enough — this section makes that concrete per entity type, now that §7 has established the locked uniform `src_ip` key:

| Entity type | Can use in-memory local state? | Needs Redis? |
|---|---|---|
| Source | Usually yes under the current source-keyed raw-topic proposal | Only where state must be shared/recovered/accessed across workers |
| Destination | Locality is insufficient for distributed-source aggregation | Proposed shared state under the current raw-topic partitioning model |
| Pair | Pair locality is not guaranteed when raw events are source-keyed | Proposed shared state under the current model |
| Connection (correlation) | `connection` and `tls` may be in different topics/partitions | Proposed short-lived shared correlation state keyed by `connection_id` |

### Redis keyspace convention by state shape

The Redpanda-topics review identified that a single key pattern should not
pretend that sliding-window counters and correlation buffers have the same
storage shape. The proposed convention therefore distinguishes three
state forms:

```text
Sliding window:
irochi:feature:<entity_type>:<entity_key>:bucket:<time_bucket>

Tumbling window:
irochi:feature:<entity_type>:<entity_key>:window:<window_id>

Session / correlation:
irochi:feature:<entity_type>:<entity_key>:correlation:<correlation_id>
```

The intended model is:

```text
sliding
→ atomic per-time-bucket counters
→ aggregate relevant buckets when evaluating the window

tumbling
→ one accumulator per known window instance

session / correlation
→ one short-lived state record per logical session/correlation
```

The exact key naming, bucket width, window identifiers, and TTL values remain
PROPOSED / OPEN.

TTL should reflect the corresponding state lifetime plus an appropriate
grace period for late/duplicate delivery.

### Carried-forward atomicity rule

As already agreed for raw-event dedup in `REDPANDA_TOPICS_DRAFT_v5.md` §12: if `event_id`-based deduplication is used when updating any of the above state, the state update and the dedup marker must be committed atomically (single Redis transaction/Lua script), or the state update itself must be made idempotent by construction. This applies uniformly to all four entity types above, not just the case that prompted it.

### Status

**PROPOSED / OPEN**, same as the underlying dedup mechanism it depends on.

---

## 10. Candidate Downstream Publication Model

### Candidate topics

This section is continuity guidance for the later Detector Input/Output design. It does not finalize downstream topic names, feature payloads, or consumer contracts.

One topic per detector domain, mirroring the "one raw topic per `event_type`" pattern from the Redpanda draft:

| Topic | `detector_domain` | Consumer |
|---|---|---|
| `irochi.features.ddos.v1` | `ddos` | DDoS Detector |
| `irochi.features.recon.v1` | `recon` | Recon Detector |
| `irochi.features.dns.v1` | `dns` | DNS/DGA/Tunneling Detector |
| `irochi.features.tls_c2.v1` | `tls_c2` | TLS/C2 Detector |
| `irochi.features.exfil.v1` | `exfil` | Exfiltration Detector |

Naming convention: `irochi.features.<domain>.v<schema_major>`, consistent with the raw-topic convention and the canonical event's `schema_version` field.

### Partition key for feature topics is not the same open question as for raw topics

This is worth stating explicitly because it looks like the same problem but isn't: by the time a feature record is emitted, its entity's state has already been correctly assembled — via Redis where §9 requires it — *before* publication. So, unlike the raw topics, a feature topic's partition key can simply equal its own `entity_key` without reintroducing the locality-vs-correctness tension `REDPANDA_TOPICS_DRAFT_v5.md` had to work through. Correctness was already settled upstream; the feature-topic key only has to serve fan-out/ordering to the one consuming detector.

### Status

**PROPOSED.**

---

## 11. Retention & Cleanup Policy

Unlike the raw topics — which represent an observation stream and were correctly assigned `cleanup.policy = delete` — feature topics are closer to a per-entity "latest known state" changelog, which is exactly what `compact` is designed for. But this is a genuine trade-off, not a clear win, so it is presented as such rather than decided here:

| Option | Benefit | Risk |
|---|---|---|
| `delete`, short retention (≈ longest window length + buffer, TBD once §8 durations are known) | Simple, matches the raw-topic mental model, safe default | Detectors that want short-term trend/history across several past windows lose it once records age out |
| `compact` | Naturally keeps only the latest value per `entity_key` — matches "detectors mostly want current state," and is cheap on storage if key cardinality stays bounded | Only helps if key cardinality is genuinely bounded (source/destination keys are; pair keys could grow large under a permissive network); also discards prior window values a detector might want for its own short trend calculation |

### Status

**PROPOSED / OPEN.** Default to `delete` with a short, TBD retention as the safe MVP starting point; revisit `compact` once detector consumption patterns (latest-value-only vs. short trend history) and observed pair-key cardinality are known.

---

## 12. Consumer Topology

Unlike the raw-event stage (one unified `irochi-feature-processing` group across three topics, because Feature Processing is one logical stage), the five detector modules are already-established logical boundaries (architecture checkpoint §11). Proposed: one consumer group per detector domain, each subscribing only to its own feature topic:

```text
irochi-detector-ddos      → irochi.features.ddos.v1
irochi-detector-recon     → irochi.features.recon.v1
irochi-detector-dns       → irochi.features.dns.v1
irochi-detector-tls-c2    → irochi.features.tls_c2.v1
irochi-detector-exfil     → irochi.features.exfil.v1
```

This does not require five separate services (checkpoint §11 still applies — a single Python process can run multiple consumer-group memberships), but it does let any one detector's consumption be scaled or paused independently, which the earlier unified raw-topic group could not offer as cleanly.

### Status

**PROPOSED.**

---

## 13. Delivery Semantics & Idempotency for Feature Records

### Proposed model

```text
At-least-once, same as the raw-event topics.
```

Because §6 requires every feature record to be a full snapshot rather than a delta, duplicate delivery of a feature record is self-correcting: a detector that applies "latest write wins" per `(entity_key, window)` is unaffected by redelivery, rebalance, or replay. This is a materially simpler duplicate-tolerance story than the raw-event topics needed, precisely because the snapshot rule in §6 removes the failure mode (double-counting) that made raw-event dedup design-sensitive.

### Status

**PROPOSED.**

---

## 14. Error / Computation-Failure Handling

Mirroring `REDPANDA_TOPICS_DRAFT_v5.md` §7's posture (DLQ as a safety net, not the primary validation mechanism): a Feature Processing computation failure (e.g. a malformed upstream event that passed Normalizer validation but breaks a specific feature calculation, or a Redis unavailability event mid-computation) should not silently drop the record or stall the worker.

Proposed: reuse the same shared-DLQ pattern (`irochi.features.dlq.v1`), carrying at minimum:

```text
detector_domain
entity_type / entity_key (where available)
failure_stage
failure_reason
original raw event_id(s) that were being processed, where available
```

Exact retry/backoff behaviour is deferred, same as the raw-event DLQ.

### Status

**PROPOSED.**

---

## 15. Serialization

**JSON**, for the same reasons as the raw-event topics (simple to inspect, easy Python integration, low operational overhead for the prototype). No schema registry, consistent with the earlier decision.

### Status

**PROPOSED.**

---

## 16. State-Management Risk Controls

### 16.1 DDoS destination-state contention

Destination-centric DDoS aggregation can create Redis hot-key contention during the exact high-rate conditions the state is intended to detect.

A naive read-modify-write pattern:

```text
read
→ modify
→ write
```

should be avoided for high-rate counters.

**Proposed approach:** use atomic counter operations such as `INCR`/`HINCRBY` against time-bucketed counters and aggregate those buckets when reading the window.

If measurement later shows that one victim key remains a bottleneck, logical destination-key sharding may be evaluated. Sharding is not locked and should only be introduced if benchmark evidence justifies it.

### 16.2 Pair-state cardinality control

Pair entities can have very high cardinality because many normal
source→destination relationships are one-off.

Avoid allocating full beacon-periodicity state for every newly seen pair.

**Proposed two-tier model:**

```text
Tier 1
lightweight repeat/existence tracking
        ↓
promotion threshold
        ↓
Tier 2
full periodicity/inter-arrival state
        ↓
feature record emission
```

**Tier 1 is internal gating state only.** A newly observed or one-off pair does
not emit a beaconing feature record merely because it entered Tier 1.

A pair is promoted to Tier 2 only after it satisfies the eventual repeat
criteria. Tier 2 owns the richer inter-arrival/periodicity state and is the
state from which beaconing feature records are emitted.

Exact promotion thresholds, eviction policy, and memory budget remain open.

### 16.3 Feature Processing internal scaling

Feature Processing remains one logical architecture stage, but its internal execution model is OPEN.

A single connection event can contribute to DDoS, Recon, Exfiltration, and C2 processing, while these workloads have different computational costs.

Evaluate later:

```text
Model A — one Feature Processing consumer group with internal fan-out

Model B — multiple domain-specific consumer groups reading raw topics
```

Model B provides more independent scaling/failure isolation but increases read amplification.

This decision must be benchmark-driven and must not create unnecessary microservices.

---

## 17. Operational Metadata vs Observability

Feature records may carry `computed_at`, `revision`, window timing, correlation status, and provenance for record-level freshness and explainability.

General pipeline health remains in the existing observability layer:

```text
Prometheus
Grafana
Redpanda consumer-group lag
CPU/RAM/throughput metrics
```

Do not re-create pipeline-wide monitoring by adding a second health system into every feature record.

---

## 18. Provenance / Explainability Hook

Architecture checkpoint §1 frames the system's job as producing **explainable** security alerts. That requirement will land on the Alert Schema, but it depends on whatever provenance feature records choose to carry now — if a feature record is emitted with no trace back to the raw events that produced it, the eventual Alert Schema cannot explain *why* a detector fired without redesigning this layer.

This draft flags a generic `provenance` field (§5 envelope) as the hook for that need, but deliberately does not resolve its shape here, because the right answer depends on volume: an enrichment or correlation record naturally has one or two contributing `event_id`s and can list them directly, but a windowed aggregate over a busy source could have thousands of contributing events, where an exhaustive list is impractical and a representative sample, a count, or a compact summary (e.g. min/max/count of contributing timestamps) may be more appropriate.

### Open note: forced early emission

The `complete` / `partial` / `late_amendment` concept may eventually apply
to windowed records that are emitted before their natural closure because
of a forced flush, shutdown, or bounded max-wait condition.

This is intentionally an OPEN consideration until an actual early-flush
requirement exists.

### Status

**OPEN.** Carried forward as an explicit input to the future Detector I/O and Alert Schema design steps, not resolved here.

---

## 19. Relationship Between Feature Processing and Other Components

```text
irochi.events.connection.v1  ─┐
irochi.events.dns.v1         ─┼──> Feature Processing (irochi-feature-processing)
irochi.events.tls.v1         ─┘         |
                                         v
                    (enrichment / windowed / correlation,
                     entity state in-memory + Redis per §9)
                                         |
             +---------------+---------------+---------------+---------------+
             v               v               v               v               v
   features.ddos.v1  features.recon.v1  features.dns.v1  features.tls_c2.v1  features.exfil.v1
             |               |               |               |               |
             v               v               v               v               v
   irochi-detector-ddos  -recon         -dns            -tls-c2         -exfil
```

Boundaries carried forward unchanged from the Redpanda draft: React never talks to Redpanda, PostgreSQL, or Redis directly; Redpanda is not the durable alert source of truth; detector modules remain logically distinct without being mandated as separate services.

---

## 20. What This Schema Does NOT Do

- Does not finalize window durations (§8) or the `retention.bytes`/`amplification_ratio` numbers already deferred upstream.
- Does not finalize Detector Input/Output contracts — this defines what a detector *receives*, not what it *decides* or *emits*.
- Does not define the Alert Schema, though §18 flags a dependency the Alert Schema will need.
- Does not lock the Redis keyspace convention (§9) beyond a proposed shape.
- Does not change any Canonical Event Schema field.
- Is not a reason to create one topic per feature rather than per detector domain.

---

## 21. Open Design Items

- [ ] Window durations per detector domain (§8) — pending benchmark/dataset review
- [ ] Entity-keying for UDP amplification/asymmetry metrics (§4) — tied to the existing open `amplification_ratio` capture-point question
- [x] Redpanda raw-topic partition key — **LOCKED** as uniform `src_ip` (§7), recorded in Redpanda v4 §4 and BD-009
- [ ] Feature-topic retention/cleanup policy: `delete` vs. `compact` (§11)
- [ ] Long-window vs. 24h raw-retention recovery risk (§8) — whether Feature Processing needs its own state checkpointing
- [ ] Shape of provenance for high-volume windowed records (§18)
- [ ] Redis keyspace convention and TTL policy (§9) — proposed shape, not locked
- [ ] Exact retry/backoff behaviour for the feature DLQ
- [ ] DDoS Redis hot-key mitigation details (§16.1)
- [ ] Pair-state promotion/eviction policy (§16.2)
- [ ] Feature Processing internal scaling model
- [ ] Snapshot `revision` monotonicity implementation
- [ ] Late correlation timeout/amendment policy
- [ ] Mechanism for `repeated-destination behaviour`
- [ ] Confirm semantics of `windowed transfer volume` / `large-transfer indicators` (per-connection vs. session/bounded aggregate)

### Explicitly NOT being decided here

- Detector Input/Output contracts
- Alert Schema
- PostgreSQL schema
- Final FastAPI routes
- Final ML/detector implementation

---

## 22. Review Checklist

Before promoting this document from DRAFT to FINAL, verify:

- [ ] All section headings and embedded cross-references resolve correctly.
- [ ] Every feature listed in architecture checkpoint §12/§14/§15 is accounted for in §4's mapping.
- [ ] Mechanism assignment (enrichment / windowed / correlation) matches whether the feature genuinely needs a window.
- [ ] Entity-type assignment matches which host(s) the feature actually describes (watch for source/destination naming confusion, as with `source_ip_entropy`).
- [x] The raw-topic partition-key decision in §7 is explicitly approved and inherited as a LOCKED upstream decision; partition count remains open.
- [ ] No window duration, retention number, or TTL value has been hard-coded without a benchmark basis.
- [ ] The snapshot-not-delta rule (§6) is reflected in whatever Feature Processing implementation follows.
- [ ] Redis keyspace convention (§9) is either accepted or explicitly revised before implementation begins.

---

## 23. Decision Status Summary

| Design Item | Status |
|---|---|
| Three-mechanism typology (enrichment / windowed / correlation) | **PROPOSED** |
| Four-entity typology (source / destination / pair / connection) | **PROPOSED** |
| Detector-to-entity-and-mechanism mapping | **PROPOSED** |
| Feature record envelope shape | **PROPOSED** |
| Snapshot-not-delta rule | **PROPOSED PROCESSING INVARIANT** |
| Raw-topic partition key = uniform `src_ip` | **LOCKED — inherited from Redpanda v4 §4 / BD-009** |
| Window-type taxonomy (Tumbling/Sliding/Session) | **LOCKED** |
| Feature-level window mapping | **PROPOSED** |
| Window durations | **OPEN — pending benchmark** |
| Redis keyspace convention | **PROPOSED / OPEN** |
| One feature topic per detector domain | **PROPOSED** |
| Feature-topic partition key = entity key | **PROPOSED** |
| Feature-topic retention: `delete` vs `compact` | **OPEN** |
| Per-detector consumer groups | **PROPOSED** |
| At-least-once delivery for feature records | **PROPOSED** |
| Shared feature DLQ | **PROPOSED** |
| JSON serialization | **PROPOSED** |
| Generic `provenance` hook | **OPEN** |
| `correlation_status` | **PROPOSED / OPEN** |
| `revision` freshness/order mechanism | **PROPOSED / OPEN** |
| Pair-state two-tier tracking | **PROPOSED / OPEN** |
| DDoS atomic counter strategy | **PROPOSED / OPEN** |
| Feature Processing internal scaling | **OPEN** |

No item in this table should be treated as locked until the project lead approves it.

---

## 24. Next Design Step

```text
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

Detector Input/Output design should treat this document's feature-topic layout and record shape as fixed inputs, and should explicitly resolve the provenance question (§18) before Alert Schema design begins, since alert explainability depends on it.

---

## 25. Final Status

**DRAFT v5 — awaiting project-lead/team review.**

No Feature/Window topics or consumers should be implemented in code from this document until the proposed design is explicitly reviewed and approved.
