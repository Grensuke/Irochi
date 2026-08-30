# SIH26145 — FEATURE / WINDOW SCHEMA (DRAFT v7)

> **Status:** DRAFT — Redis state modeling pass complete; individual section statuses vary (see §23). Requires project-lead / team review before promotion to `_FINAL`.
>
> **Continues from:** `docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md`, `docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md` (§9, §10, §12, §14, §15), and `docs/architecture/REDPANDA_TOPICS_DRAFT_v5.md`.
>
> **Scope:** This document defines what a **feature/window record** is, how derived signals are computed and keyed, and how derived-state processing relates to the approved Redpanda design. It does **not** finalize Detector I/O contracts, Alert Schema, or PostgreSQL schema — those remain later steps.

### v6 → v7 revision summary

- Added §9a Redis State Model: comprehensive state inventory, per-detector state shapes, deduplication/atomicity strategy, snapshot/revision boundary, in-memory vs Redis policy, keyspace governance, TTL principles, hot-key risk mitigation, state lifecycle, and recovery/rebuild considerations.
- Locked four foundational items via explicit project-lead approval (Task 16a / AR-01):
  - Snapshot-not-delta rule → LOCKED PROCESSING INVARIANT
  - DDoS atomic counter strategy (INCR/HINCRBY baseline) → LOCKED
  - Directional pair key `(src_ip, dst_ip)`, not canonicalized → LOCKED
  - Tier 1 / Tier 2 pair-state split (existence and roles) → LOCKED; promotion/eviction/budget remain OPEN
- Shortened §16.1 and §16.2 to brief risk-control summaries with cross-references to §9a (Option b — no section renumbering).
- Distinguished distinct-count estimation (HyperLogLog baseline) from entropy estimation (frequency/distribution state required); kept final implementation choice OPEN for both.
- Updated §21, §22, §23, §25 to reflect Redis state modeling at PROPOSED level.
- Fixed §7 status line: "Redpanda v4 §4" → "Redpanda v5 §4".

### v5 → v6 revision summary

- Locked the three supported window mechanisms (Tumbling / Sliding / Session) as the window taxonomy.
- Resolved feature-level mechanism assignments for DDoS (Sliding), Recon breadth (Tumbling), Recon rate (Sliding), DNS/tunneling query_frequency (Sliding), DNS/tunneling record-type distribution (Tumbling), Beaconing primary (Sliding), and Exfiltration rate (Sliding).
- Documented Recon's accepted MVP boundary-evasion risk for Tumbling breadth features.
- Moved UDP amplification/asymmetry explicitly OUT OF SCOPE FOR MVP.
- Retained exfiltration transfer-volume/large-transfer semantics and repeated-destination behaviour as OPEN.
- Preserved exact durations, bucket widths, and session gaps as OPEN / benchmark-driven.
- Added Window Type column to the §4 mapping table.
- Updated §8, §21, §22, §23, §24, and §25 to reflect resolved and remaining-open items consistently.
- Added design-chain discipline note: Detector I/O may begin on the approved envelope shape, but detector-specific payloads depend on feature mappings that remain PROPOSED/OPEN.

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

| Detector domain | Feature | Mechanism | Entity | Window Type | Primary raw topic(s) |
|---|---|---|---|---|---|
| DDoS | `packet_rate`, `byte_rate`, `syn_ratio` | Windowed | **Destination** | **Sliding** | `connection` |
| DDoS | `source_ip_entropy` | Windowed | **Destination** | **Sliding** | `connection` |
| DDoS | UDP amplification/asymmetry metrics | Windowed | — | — | `connection` |
| Recon | `unique_destination_ports`, `unique_destination_hosts`, `connection_fan_out` | Windowed | **Source** | **Tumbling** | `connection` |
| Recon | `scan_rate` | Windowed | **Source** | **Sliding** | `connection` |
| DNS/DGA | `domain_entropy`, `query_length`, `n_gram_score`, label-length statistics | **Enrichment** | n/a (per-event) | n/a | `dns` |
| DNS/tunneling | `query_frequency` | Windowed | **Source** | **Sliding** | `dns` |
| DNS/tunneling | record-type distribution | Windowed | **Source** | **Tumbling** | `dns` |
| TLS/C2 | `ja3_blacklist_match` | **Enrichment** | n/a (per-event lookup) | n/a | `tls` |
| TLS/C2 | Flow-level join (attach TLS outcome to its flow's byte/packet counts) | **Correlation** | **Connection** | n/a | `connection` + `tls` |
| C2 beaconing (general) | `inter_arrival_time`, `beacon_periodicity`, periodicity variance, regularity, connection frequency | Windowed | **Pair** | **Sliding** | `connection` (checkpoint §12.2: *"a general flow/timing signal, not a TLS-only signal"*) |
| C2 beaconing (general) | `repeated-destination behaviour` | Windowed | **Pair** | **OPEN** | `connection` |
| Exfiltration | `outbound_inbound_ratio`, `byte_rate` | Windowed | **Source** | **Sliding** | `connection` |
| Exfiltration | `windowed transfer volume`, `large-transfer indicators` | Windowed | **Source** | **OPEN** | `connection` |

**UDP amplification/asymmetry:** **OUT OF SCOPE FOR MVP.** The capture-point / sensor-placement question (architecture checkpoint §12.1 / `amplification_ratio`) is not resolved and is not required for the MVP detector set. The row is retained for architectural continuity; entity, window type, and feature formulation remain undecided until a post-MVP revisit.

Four things worth flagging explicitly because they are easy to miss on a first read:

1. **C2 beaconing is pair-entity, and its primary channel is `connection`, not `tls`.** This matters for §7 below — a partition-key design that only gives pair locality to the `tls` topic does not actually help the primary beaconing signal.
2. **`source_ip_entropy` is a destination-entity feature.** It is easy to assume anything with "source" in the name is source-keyed. It isn't — it describes the diversity of sources converging on one destination, so it lives with the DDoS/destination row, not the source-entity rows.
3. **Recon breadth features use Tumbling as an accepted MVP mechanism.** Window-boundary pacing can evade per-window breadth thresholds; this is an accepted MVP limitation. Fast vs slow scan variation is expected to be handled through window duration/threshold tuning within the chosen mechanism for MVP. A different mechanism remains a post-MVP consideration if evaluation shows significant boundary/evasion problems.
4. **`repeated-destination behaviour` and exfiltration transfer-volume/large-transfer semantics remain OPEN** — they cannot be cleanly resolved without additional specification.

### Status

**PROPOSED (with resolved rows as documented above).** The mechanism/entity/window-type assignments follow directly from already-decided threat-to-signal reasoning; nothing here re-opens those decisions. Unresolved rows are explicitly marked OPEN.

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
| `entity_type` | enum | Yes | `source`, `destination`, `pair`, or `connection` (AR-02: Required for all mechanisms including enrichment) |
| `entity_key` | string | Yes | The actual key value (`src_ip`, `dst_ip`, `"src_ip\|dst_ip"`, or `connection_id`) (AR-02: Required for all mechanisms) |
| `window_type` | enum | Conditional | `tumbling`, `sliding`, or `session`; present only for `windowed` records |
| `window_start` / `window_end` | int64 | Conditional | Epoch microseconds; present only for `windowed` records |
| `computed_at` | int64 | Yes | Time Feature Processing emitted the record (epoch microseconds) — mirrors `ingest_timestamp`'s role: observability/lag measurement, not a detection feature |
| `schema_version` | string | Yes | Version of the feature-record contract |
| `provenance` | object | Optional | References/summary describing the raw events contributing to the record; exact shape remains open |

### `detector_domain` ↔ `detector_id` Mapping

The `detector_domain` field is the Feature/Window routing/domain identity. It explicitly bridges to the canonical `detector_id` identity used downstream in the Alert layer:

- `ddos` → `ddos_detector`
- `recon` → `recon_detector`
- `dns` → `dns_dga_tunnel_detector`
- `tls_c2` → `tls_c2_detector`
- `exfil` → `exfiltration_detector`

The upcoming Detector I/O design will explicitly bridge the two. This mapping is not five new detector implementations; it just clarifies how the short domain names in the feature envelope map to the canonical detector identities.

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

`REDPANDA_TOPICS_DRAFT_v5.md` §4 and `docs/backend/BACKEND_DECISIONS.md` BD-009 now record Candidate A as locked:
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
in `REDPANDA_TOPICS_DRAFT_v5.md` §4 and `docs/backend/BACKEND_DECISIONS.md` BD-009. If a future benchmark or
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

**LOCKED (inherited from Redpanda v5 §4 and recorded in BD-009).** The lock applies to the raw
partition key only; partition counts and other Redpanda choices remain open.

---

## 8. Window Model

### Window taxonomy

The Feature/Window layer supports exactly three window mechanisms:

| Window type | Behaviour | Current use |
|---|---|---|
| Tumbling | Fixed, non-overlapping | Bounded snapshots/counts where interval-level aggregation is appropriate |
| Sliding | Continuously recomputed over a bounded rolling horizon | Time-sensitive rates, source/destination behaviour, and pair-timing features |
| Session | Closes after a gap of inactivity | Bounded activity/transfer sessions where session closure is semantically meaningful |

"Incremental rolling computation" is an implementation technique inside Sliding, not a separate mechanism. Do not invent a fourth mechanism.

**Status:** **LOCKED.** The three mechanism types are the supported taxonomy.

### Feature-level mechanism assignments

The authoritative per-feature mechanism/entity/window-type mapping is in §4. This subsection documents the resolved assignments and remaining open items in prose form.

**Resolved assignments (v6):**

- **DDoS** (`packet_rate`, `byte_rate`, `syn_ratio`, `source_ip_entropy`): **Destination / Sliding.** Time-sensitive victim-side burst/diversity signal.
- **Recon breadth** (`unique_destination_ports`, `unique_destination_hosts`, `connection_fan_out`): **Source / Tumbling.** Bounded breadth measurement over an observation interval.
- **Recon rate** (`scan_rate`): **Source / Sliding.** Rate-sensitive scan behaviour.
- **DNS/tunneling** (`query_frequency`): **Source / Sliding.** Recent DNS request rate.
- **DNS/tunneling** (record-type distribution): **Source / Tumbling.** Distribution over a bounded observation interval.
- **C2 beaconing primary** (`inter_arrival_time`, `beacon_periodicity`, periodicity variance, regularity, connection frequency): **Pair / Sliding.** Bounded rolling timing signal.
- **Exfiltration rate** (`outbound_inbound_ratio`, `byte_rate`): **Source / Sliding.** Rolling transfer-rate/directionality signal.

**Remaining OPEN:**

- **C2 beaconing:** `repeated-destination behaviour` — mechanism still needs explicit selection.
- **Exfiltration:** `windowed transfer volume`, `large-transfer indicators` — the architecture checkpoint lists these as derived signals but does not establish whether they represent per-connection properties or bounded/session-level aggregates. Do not guess; retain as OPEN.

**OUT OF SCOPE FOR MVP:**

- **DDoS:** UDP amplification/asymmetry metrics — capture-point / sensor-placement semantics (architecture checkpoint §12.1 / `amplification_ratio`) are not resolved and are not required for the MVP detector set.

### Recon Tumbling: accepted MVP limitation

Tumbling is accepted for MVP breadth features (unique destinations, fan-out). Window-boundary pacing can evade per-window breadth thresholds; this is a known MVP limitation. Fast vs slow scan variation is expected to be handled through window duration/threshold tuning within the chosen mechanism for MVP. A different mechanism remains a post-MVP consideration if evaluation shows significant boundary/evasion problems.

### Beaconing: Sliding implementation note

For beaconing, **Sliding** is the mechanism. The Sliding computation may be updated incrementally as new observations arrive; this does not introduce another window mechanism.

Beaconing is **not Session-primary**. A session inactivity threshold that is too close to the interval being detected can fragment a regular beacon sequence, so Session is not used as the primary periodicity mechanism here.

### Exfiltration scope note

The architecture checkpoint lists `windowed transfer volume` and `large-transfer indicators` as derived signals but does not specify whether they are properties of a single connection or aggregates across a bounded transfer/session. This draft therefore keeps their current **Windowed / Source** classification while making the semantic question explicit as OPEN.

### Deriving window length instead of guessing it

Consistent with architecture checkpoint §9 and the Redpanda design's refusal to invent a `retention.bytes` number before measurement, this draft does not assign specific durations. Each detector-domain window length should be derived from:

```text
time-to-signal budget
        vs.
statistical stability
```

evaluated against a representative dataset/PCAP once available.

For example, DDoS burst windows are expected to favour low latency, while low-and-slow recon/beaconing behaviour may favour longer stability. These are directional expectations only; the actual numbers remain OPEN.

### A risk worth naming now: long windows vs. the 24h raw-retention buffer

If any detector's eventual window approaches the 24-hour raw-retention horizon, a Feature Processing worker that crashes cannot always reconstruct the full window purely from Redpanda replay. Such entities may therefore need periodic state checkpointing (for example, persisted in-progress Redis state) rather than relying entirely on raw-event replay. This is an OPEN risk because the actual window lengths are not yet finalized.

### Status

- **Window-type taxonomy:** **LOCKED.**
- **Feature-level mapping:** **PROPOSED** (individual rows resolved per above; a few remain explicitly OPEN).
- **Window durations:** **OPEN** — benchmark/dataset-driven.
- **Bucket widths:** **OPEN** — benchmark/dataset-driven.
- **Session inactivity gaps:** **OPEN** — benchmark/dataset-driven.

---
## 9. State Locality & Redis Strategy

Following `REDPANDA_TOPICS_DRAFT_v5.md` §12/§21's distinction — partition key is a transport/load decision, Redis is the correctness backstop when locality isn't enough — this section makes that concrete per entity type, now that §7 has established the locked uniform `src_ip` key:

| Entity type | Can use in-memory local state? | Needs Redis? |
|---|---|---|
| Source | Usually yes under the current source-keyed raw-topic proposal | Only where state must be shared/recovered/accessed across workers |
| Destination | Locality is insufficient for distributed-source aggregation | Proposed shared state under the current raw-topic partitioning model |
| Pair | Pair locality is not guaranteed when raw events are source-keyed | Proposed shared state under the current model |
| Connection (correlation) | `connection` and `tls` may be in different topics/partitions | Proposed short-lived shared correlation state keyed by `connection_id` |

These Redis requirements are consequences of the current partitioning model, not absolute architectural mandates. If the partitioning model changes, the Redis requirement should be re-evaluated.

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

## 9a. Redis State Model

This section defines the structural Redis state required by the Feature/Window architecture. It provides state inventory, per-detector state shapes, lifecycle, atomicity, and recovery considerations so that implementation can begin without inventing key shapes or update semantics ad hoc.

**What this section does NOT finalize:**

- Exact TTL values, bucket widths, window durations, or memory limits — these remain OPEN / benchmark-driven.
- HyperLogLog vs exact-set final selection — both are documented; the choice is PROPOSED / OPEN.
- Entropy implementation algorithm — the minimum state requirements are identified; the formula is OPEN.
- Promotion thresholds, eviction policy, and memory budgets for pair state — remain OPEN.
- Correlation timeout — remains OPEN.
- Revision monotonicity implementation — the invariant is defined; the mechanism is OPEN.
- State for `repeated-destination behaviour` or exfiltration `windowed transfer volume` / `large-transfer indicators` — these features' semantics are unresolved (§4/§8); no Redis state is modeled for them.
- UDP amplification/asymmetry metrics — OUT OF SCOPE FOR MVP.

### 9a.1 State Inventory

| State ID | Feature(s) | Entity | Mechanism | Redis required? | In-memory allowed? | Redis key shape | Redis data structure | Write/update operation | Read/evaluation operation | Snapshot output | Atomicity requirement | TTL principle | Recovery consideration | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DDOS-DST-COUNTERS | `packet_rate`, `byte_rate`, `syn_ratio` | Destination | Sliding | **Yes** — destination state requires cross-worker sharing | No — destination events are scattered across source-keyed partitions | `irochi:feature:destination:<dst_ip>:bucket:<time_bucket>` | Hash | `HINCRBY` per counter field | Aggregate relevant time buckets, compute rate/ratio | DdosFeaturePayload snapshot | Atomic per-field increment (no read-modify-write) | Bucket lifetime + late-arrival grace | Replay from Redpanda within 24h raw retention; longer windows may need checkpointing | PROPOSED |
| DDOS-DST-CARDINALITY | `source_ip_entropy` — distinct source count component | Destination | Sliding | **Yes** — same cross-worker requirement as DDOS-DST-COUNTERS | No | `irochi:feature:destination:<dst_ip>:hll:<time_bucket>` | HyperLogLog | `PFADD <src_ip>` | `PFCOUNT` or `PFMERGE` across relevant buckets | Feeds into entropy estimation alongside frequency state | Atomic (PFADD is inherently idempotent) | Same as DDOS-DST-COUNTERS | Same as DDOS-DST-COUNTERS | PROPOSED |
| DDOS-DST-ENTROPY | `source_ip_entropy` — frequency/distribution component | Destination | Sliding | **Yes** | No | `irochi:feature:destination:<dst_ip>:freq:<time_bucket>` | Hash with per-source counters, or probabilistic frequency sketch (implementation choice OPEN) | `HINCRBY` per frequency bucket | Read frequency distribution, compute entropy estimate | Combined with DDOS-DST-CARDINALITY to produce entropy value | Atomic per-field increment | Same as DDOS-DST-COUNTERS | Same as DDOS-DST-COUNTERS | PROPOSED / OPEN (implementation choice) |
| RECON-SRC-BREADTH | `unique_destination_ports`, `unique_destination_hosts`, `connection_fan_out` | Source | Tumbling | Conditional — source locality may allow in-memory under current partitioning | **Yes** — source events land on the same partition under `src_ip` key | `irochi:feature:source:<src_ip>:window:<window_id>` | HyperLogLog (one per distinct-count metric per window) or Hash accumulator for fan-out count | `PFADD <dst_port>` / `PFADD <dst_ip>` / `HINCRBY fan_out 1` | `PFCOUNT` for distinct counts; `HGET` for fan-out | ReconFeaturePayload snapshot | PFADD idempotent; HINCRBY atomic | Window lifetime + grace | Replay from Redpanda within 24h retention | PROPOSED |
| RECON-SRC-RATE | `scan_rate` | Source | Sliding | Conditional — same source-locality consideration | **Yes** | `irochi:feature:source:<src_ip>:bucket:<time_bucket>` | Hash (field = `scan_count`, value = count) | `HINCRBY scan_count 1` | Aggregate relevant buckets, compute rate | Part of ReconFeaturePayload | Atomic increment | Bucket lifetime + grace | Replay within retention | PROPOSED |
| DNS-SRC-FREQ | `query_frequency` | Source | Sliding | Conditional | **Yes** | `irochi:feature:source:<src_ip>:bucket:<time_bucket>` | Hash (field = `dns_query_count`) | `HINCRBY dns_query_count 1` | Aggregate buckets, compute rate | DnsFeaturePayload windowed fields | Atomic increment | Bucket lifetime + grace | Replay within retention | PROPOSED |
| DNS-SRC-DIST | record-type distribution | Source | Tumbling | Conditional | **Yes** | `irochi:feature:source:<src_ip>:window:<window_id>` | Hash (field per record type: `A`, `AAAA`, `MX`, `TXT`, `CNAME`, etc.; value = count) | `HINCRBY <record_type> 1` | `HGETALL`, compute distribution ratios | DnsFeaturePayload windowed fields | Atomic per-field increment | Window lifetime + grace | Replay within retention | PROPOSED |
| BEACON-PAIR-T1 | (gating state — no feature output) | Pair | Sliding workflow — Tier 1 gating state | **Yes** — pair locality not guaranteed under source-keyed partitions | No | `irochi:feature:pair:<src_ip>|<dst_ip>:tier1` | Hash (fields: `count`, `first_seen`, `last_seen`) | `HINCRBY count 1`, `HSET last_seen <ts>`, conditional `HSETNX first_seen <ts>` | Check `count` against promotion threshold | None — Tier 1 does not emit feature records | Atomic via pipeline or Lua script | Tier 1 lifetime (shorter than Tier 2) | Tier 1 is lightweight; loss acceptable, pair re-enters on next observation | PROPOSED |
| BEACON-PAIR-T2 | `inter_arrival_time`, `beacon_periodicity`, periodicity variance, regularity, connection frequency | Pair | Sliding | **Yes** | No | `irochi:feature:pair:<src_ip>|<dst_ip>:tier2` | Hash (summary stats) + List or Sorted Set (bounded recent inter-arrival times) | Append new inter-arrival observation; update summary counters | Read bounded observation history; compute periodicity/variance/regularity | TlsC2FeaturePayload beaconing fields — full snapshot | Atomic append + summary update via Lua script or pipeline | Tier 2 lifetime (longer than Tier 1) | Higher-value state; may warrant checkpointing if window horizon approaches 24h | PROPOSED |
| EXFIL-SRC-RATE | `outbound_inbound_ratio`, `byte_rate` | Source | Sliding | Conditional | **Yes** | `irochi:feature:source:<src_ip>:bucket:<time_bucket>` | Hash (fields: `outbound_bytes`, `inbound_bytes`, `total_bytes`) | `HINCRBY` per directional byte counter | Aggregate buckets; compute ratio and rate | ExfilFeaturePayload snapshot | Atomic per-field increment | Bucket lifetime + grace | Replay within retention | PROPOSED |
| CORR-CONN | Flow-level join (`connection` ↔ `tls`) | Connection | Correlation | **Yes** — `connection` and `tls` events may arrive on different partitions | No | `irochi:feature:connection:<connection_id>:correlation` | Hash (fields populated incrementally as each side arrives) | `HSET` / `HMSET` for arriving side's fields | Check completeness (both sides present?) | TlsC2FeaturePayload correlation fields with `correlation_status` | Atomic field-set (HSET is inherently atomic per field) | Correlation timeout + grace | Short-lived; loss means the correlation is re-attempted on next matching event or marked partial | PROPOSED |

### 9a.2 DDoS Destination State

DDoS destination state must support four features computed over a Sliding window keyed by `dst_ip`:

- `packet_rate` — packets per unit time
- `byte_rate` — bytes per unit time
- `syn_ratio` — SYN packets / total packets (or relevant subset)
- `source_ip_entropy` — diversity/distribution of source IPs targeting one destination

#### Counter state (packet_rate, byte_rate, syn_ratio)

**Redis key:** `irochi:feature:destination:<dst_ip>:bucket:<time_bucket>`

**Data structure:** Redis Hash with atomic counter fields:

```text
fields:
  total_packets   → HINCRBY
  total_bytes     → HINCRBY
  syn_packets     → HINCRBY
```

**Write:** On each `connection` event whose `dst_ip` matches:
- Determine `time_bucket` from event timestamp
- `HINCRBY irochi:feature:destination:<dst_ip>:bucket:<time_bucket> total_packets 1`
- `HINCRBY ... total_bytes <orig_bytes + resp_bytes>`
- `HINCRBY ... syn_packets 1` (if SYN flag present)

**No read-modify-write.** Each update is a single atomic increment.

**Evaluation:** To compute the Sliding window snapshot:
1. Determine the set of time buckets covering the current window `[window_start, window_end]`
2. `HGETALL` each relevant bucket (pipeline for efficiency)
3. Sum counters across buckets
4. Compute: `packet_rate = total_packets / window_duration`, `byte_rate = total_bytes / window_duration`, `syn_ratio = syn_packets / total_packets`

#### Distinct-count state (source_ip_entropy — cardinality component)

`source_ip_entropy` is a **destination-entity** feature that measures the diversity of source IPs converging on one destination. It requires **two** kinds of information:

1. **Distinct source count** — how many unique source IPs were seen
2. **Frequency distribution** — how traffic is distributed across those sources (entropy cannot be computed from cardinality alone)

**Distinct count — HyperLogLog baseline (PROPOSED):**

**Redis key:** `irochi:feature:destination:<dst_ip>:hll:<time_bucket>`

```text
PFADD irochi:feature:destination:<dst_ip>:hll:<time_bucket> <src_ip>
```

HyperLogLog provides O(1) memory (~12KB per key) with ~0.81% standard error. It is inherently idempotent — adding the same `src_ip` twice has no effect.

For evaluation across a Sliding window: `PFMERGE` across relevant time-bucket HLLs, then `PFCOUNT`.

**Alternative:** Exact Redis Set (`SADD` / `SCARD`). Exact count, but memory is unbounded under attack conditions (millions of unique source IPs targeting one destination during a DDoS flood — exactly the condition this feature is designed to detect). Not recommended as the baseline for MVP.

**Frequency/distribution state — entropy component (OPEN):**

HyperLogLog cannot provide entropy by itself; entropy requires frequency distribution information.

**Minimum state required:** A bounded approximation of the per-source frequency distribution within each time bucket. Candidate approaches include:

- **Hash with per-source counters:** `HINCRBY irochi:feature:destination:<dst_ip>:freq:<time_bucket> <src_ip> <packet_count>` — exact but memory proportional to unique source count per bucket
- **Probabilistic frequency sketch** (e.g. Count-Min Sketch): bounded memory, approximate frequency estimation — but Redis does not natively support CMS; would require a module or application-level implementation
- **Binned/bucketed frequency histogram:** group source IPs into a fixed number of frequency bins — bounded memory, approximate entropy

**Status:** The need for frequency/distribution state beyond HLL is identified. The exact implementation (per-source hash vs sketch vs histogram) remains **OPEN**. The entropy feature requires both cardinality and frequency components; neither alone is sufficient.

### 9a.3 Recon Source State

Recon source state must support two structurally different feature classes:

**Tumbling breadth features:** `unique_destination_ports`, `unique_destination_hosts`, `connection_fan_out`

**Sliding rate feature:** `scan_rate`

#### Breadth state (Tumbling)

These are distinct-count problems. `unique_destination_ports` counts how many distinct destination ports a source contacted within a Tumbling window. `unique_destination_hosts` counts distinct destination IPs. `connection_fan_out` counts total connections (a simple counter, not a distinct-count problem).

**Redis key:** `irochi:feature:source:<src_ip>:window:<window_id>`

The `window_id` is derived from the Tumbling window boundaries (e.g. epoch-based: `floor(timestamp / window_duration)`).

**Distinct-count state — HyperLogLog baseline (PROPOSED):**

```text
PFADD irochi:feature:source:<src_ip>:window:<window_id>:ports <dst_port>
PFADD irochi:feature:source:<src_ip>:window:<window_id>:hosts <dst_ip>
```

Same trade-off as DDoS cardinality: HyperLogLog is O(1) memory and idempotent, with ~0.81% standard error. An exact Set (`SADD`/`SCARD`) is an alternative but memory is proportional to the number of unique destinations — for aggressive scanners this can be very large.

**Fan-out counter:**

```text
HINCRBY irochi:feature:source:<src_ip>:window:<window_id> connection_fan_out 1
```

Simple atomic counter — no distinct-count problem.

**Evaluation:** At Tumbling window closure (or on-demand):
1. `PFCOUNT` for distinct port/host counts
2. `HGET` for fan-out
3. Emit ReconFeaturePayload snapshot

**In-memory alternative:** Under the current `src_ip` partition key, source-entity events land on the same Redpanda partition. A single Feature Processing worker handling that partition can maintain Tumbling window state in memory. Redis is needed only if:
- Multiple workers share the same partition (consumer group rebalance)
- State must survive worker restart within the same window
- Cross-worker visibility is required

**Status:** PROPOSED. The in-memory vs Redis boundary is a deployment-time decision per the policy in §9a.10.

#### Rate state (Sliding)

`scan_rate` uses Sliding time-bucketed counters, identical in structure to DDoS counters:

**Redis key:** `irochi:feature:source:<src_ip>:bucket:<time_bucket>`

```text
HINCRBY irochi:feature:source:<src_ip>:bucket:<time_bucket> scan_count 1
```

Evaluation: aggregate relevant buckets over the Sliding window, compute rate.

**Status:** PROPOSED.

### 9a.4 DNS Source State

Two distinct state shapes:

#### query_frequency — Sliding

Counts DNS queries per source over a Sliding window.

**Redis key:** `irochi:feature:source:<src_ip>:bucket:<time_bucket>`

```text
HINCRBY irochi:feature:source:<src_ip>:bucket:<time_bucket> dns_query_count 1
```

Evaluation: aggregate buckets, compute queries/second.

**Note:** This key may share the same Redis Hash as Recon and Exfiltration source-keyed Sliding buckets if bucket width is the same. Whether to use shared or per-domain hashes is an implementation choice — shared saves keys; per-domain is simpler to reason about. This is **PROPOSED / OPEN**.

#### Record-type distribution — Tumbling

Tracks the distribution of DNS record types (A, AAAA, MX, TXT, CNAME, etc.) per source within a Tumbling window.

**Redis key:** `irochi:feature:source:<src_ip>:window:<window_id>`

**Data structure:** Redis Hash with one field per record type:

```text
HINCRBY irochi:feature:source:<src_ip>:window:<window_id> A 1
HINCRBY irochi:feature:source:<src_ip>:window:<window_id> TXT 1
```

Evaluation: `HGETALL`, compute distribution ratios (e.g. TXT proportion as a DNS tunneling signal).

**Note:** DNS/DGA enrichment features (`domain_entropy`, `query_length`, `n_gram_score`, label-length statistics) are per-event computations (§4 — Enrichment mechanism). They require **no** Redis state and are not modeled here.

**Status:** PROPOSED.

### 9a.5 Beaconing Pair State

Beaconing pair state uses directional pair keys:

```text
(src_ip, dst_ip) ≠ (dst_ip, src_ip)
```

The pair key is **not** sorted or canonicalized (§3 — LOCKED).

**Redis key encoding for pairs:** `<src_ip>|<dst_ip>`. `|` is the current proposed delimiter; alternative delimiters or structured encoding remain implementation choices.

#### Tier 1 — Lightweight gating state

**Purpose:** Track whether a pair has been observed enough times to warrant full periodicity analysis. Tier 1 is internal gating state only — it does **not** emit feature records.

**Redis key:** `irochi:feature:pair:<src_ip>|<dst_ip>:tier1`

**Data structure:** Redis Hash:

```text
fields:
  count       → total observations
  first_seen  → epoch timestamp of first observation
  last_seen   → epoch timestamp of most recent observation
```

**Write:** On each `connection` event for a (src_ip, dst_ip) pair:
```text
HINCRBY  irochi:feature:pair:<src_ip>|<dst_ip>:tier1 count 1
HSET     irochi:feature:pair:<src_ip>|<dst_ip>:tier1 last_seen <timestamp>
HSETNX   irochi:feature:pair:<src_ip>|<dst_ip>:tier1 first_seen <timestamp>
```

These can be pipelined or wrapped in a Lua script for atomicity.

**Promotion check:** If `count >= promotion_threshold` (OPEN — exact value TBD), promote to Tier 2.

**Tier 1 does not produce feature records.** A newly observed or infrequent pair never generates a beaconing feature record.

#### Tier 2 — Full periodicity/inter-arrival state

**Purpose:** Maintain the state needed to compute periodicity, variance, regularity, and connection frequency for pairs that passed Tier 1 gating. Tier 2 is the feature-producing state.

**Redis key:** `irochi:feature:pair:<src_ip>|<dst_ip>:tier2`

**Data structure:** Redis Hash (summary statistics) + Redis List or Sorted Set (bounded observation history):

**Summary fields (Hash):**
```text
  connection_count     → total connections since promotion
  last_seen            → most recent observation timestamp
  last_iat             → most recent inter-arrival time
  sum_iat              → running sum of inter-arrival times
  sum_iat_sq           → running sum of squared inter-arrival times (for variance)
```

**Observation history (bounded List or Sorted Set):**
```text
  irochi:feature:pair:<src_ip>|<dst_ip>:tier2:history
  → bounded circular buffer of recent inter-arrival times or timestamps
  → used for periodicity/regularity computation at evaluation time
  → max length TBD (OPEN — bounded by memory budget)
```

**Write:** On each observation after promotion:
1. Compute `inter_arrival_time = current_timestamp - last_seen`
2. Update summary fields atomically (Lua script or pipeline)
3. Append to bounded history (`RPUSH` + `LTRIM` for List; `ZADD` + `ZREMRANGEBYRANK` for Sorted Set)

**Evaluation:** Read summary stats and history; compute:
- `beacon_periodicity` = mean inter-arrival time
- variance / regularity from `sum_iat`, `sum_iat_sq`, and/or the raw history
- `connection_frequency` from connection_count and time span

The specific statistical formula for periodicity detection (e.g. coefficient of variation, entropy of inter-arrival times, autocorrelation) is **not** selected here — only the state shape needed to support any reasonable formula.

**What is stored vs derived at evaluation time:**
- **Stored:** raw inter-arrival observations (bounded), running sums, counts, timestamps
- **Derived at evaluation:** periodicity score, regularity score, variance — these are computed from stored state during snapshot production

**`repeated-destination behaviour`** remains an explicitly OPEN feature (§4/§8). No Redis state is modeled for it because its semantics and mechanism are unresolved.

**Promotion threshold, eviction policy, and memory budget remain OPEN.**

**Status:** PROPOSED.

### 9a.6 Exfiltration Source State

Exfiltration source state supports two resolved Sliding features:

- `outbound_inbound_ratio` — ratio of outbound to inbound bytes
- `byte_rate` — transfer rate

**Redis key:** `irochi:feature:source:<src_ip>:bucket:<time_bucket>`

**Data structure:** Redis Hash with directional byte counters:

```text
fields:
  outbound_bytes   → HINCRBY
  inbound_bytes    → HINCRBY
  total_bytes      → HINCRBY (optional — derivable from outbound + inbound)
```

**Write:** On each `connection` event:
```text
HINCRBY irochi:feature:source:<src_ip>:bucket:<time_bucket> outbound_bytes <orig_bytes>
HINCRBY irochi:feature:source:<src_ip>:bucket:<time_bucket> inbound_bytes <resp_bytes>
```

**Evaluation:** Aggregate buckets over the Sliding window, compute `outbound_inbound_ratio = outbound_bytes / inbound_bytes` and `byte_rate = total_bytes / window_duration`.

**`windowed transfer volume` and `large-transfer indicators`** remain explicitly OPEN because their semantics (per-connection vs session/bounded aggregate) are unresolved (§4/§8). **No Redis state is modeled for them.**

**In-memory alternative:** Same source-locality consideration as Recon — in-memory is viable under source-keyed partitioning if cross-worker sharing and restart-survival are not required.

**Status:** PROPOSED.

### 9a.7 Connection Correlation Buffer

The `connection` ↔ `tls` correlation joins records that share a `connection_id` across different raw topics.

**Redis key:** `irochi:feature:connection:<connection_id>:correlation`

**Data structure:** Redis Hash with fields populated incrementally as each side arrives:

```text
fields:
  # Populated when connection event arrives:
  conn_received      → 1 (marker)
  orig_bytes         → value
  resp_bytes         → value
  duration           → value
  conn_timestamp     → epoch

  # Populated when tls event arrives:
  tls_received       → 1 (marker)
  ja3                → value
  ja3s               → value
  ja3_blacklist_match → 0 or 1
  tls_timestamp      → epoch

  # Metadata:
  correlation_status → "partial" | "complete" | "late_amendment"
  created_at         → epoch (for timeout calculation)
```

**Arrival/update behaviour:**
1. First event (either `connection` or `tls`) creates the Hash with its side's fields and sets `correlation_status = "partial"`.
2. Second event adds its side's fields and sets `correlation_status = "complete"`.
3. If a third observation arrives after completion, it is treated as a `late_amendment` — the existing fields may be updated but the correlation is already emitted.

A duplicate delivery of an already-processed event must not create a new
late_amendment or increment the revision. Event identity must be checked
before any correlation status transition or amendment emission.

**Timeout:** If only one side arrives within the correlation timeout (OPEN — exact value TBD), the buffer remains `partial`. At evaluation/flush time, a partial correlation is emitted with `correlation_status = "partial"` carrying only the available fields.

**Completion condition:** Both `conn_received = 1` and `tls_received = 1`.

**Revision interaction:** A complete correlation snapshot supersedes a partial one for the same `connection_id`. If a late TLS event arrives after a partial correlation was already emitted, a new snapshot with `correlation_status = "late_amendment"` and a higher `revision` is emitted.

**Status:** PROPOSED.

### 9a.8 Deduplication & Atomicity

#### Principle

When updating Redis state from raw Redpanda events, the state update and any dedup marker must either:

1. **Be atomic together** — single Redis transaction, Lua script, or pipeline guaranteeing all-or-nothing execution, OR
2. **The state update must be idempotent by construction** — processing the same event twice produces the same end state as processing it once.

This principle was already established in §9 (carried forward from `REDPANDA_TOPICS_DRAFT_v5.md` §12).

#### How it applies per state type

**Bucket counters (DDoS, Recon rate, DNS, Exfiltration):**
- `HINCRBY` is **not** inherently idempotent — incrementing twice for the same event double-counts.
- **Option A:** Guard with `event_id`-based dedup: check a dedup set/key before incrementing, atomically via Lua script.
- **Option B:** Make the counter idempotent by including the `event_id` in the increment logic (e.g. `SADD` to a dedup set + `HINCRBY` in one Lua transaction; skip if already in set).
- **Status:** PROPOSED — the exact dedup mechanism is an implementation choice.

**HyperLogLog (DDoS cardinality, Recon distinct-count):**
- `PFADD` is **inherently idempotent** — adding the same element twice has no effect on the HLL's internal state.
- No additional dedup mechanism is required for HLL updates.

**Pair state — Tier 1:**
- `HINCRBY count 1` for the same event would overcount. Same dedup consideration as bucket counters.
- `HSETNX first_seen` is idempotent. `HSET last_seen` with the same timestamp is idempotent.
- The `count` field requires dedup protection or idempotent construction.

**Pair state — Tier 2:**
- Appending the same inter-arrival observation twice would corrupt periodicity statistics.
- Requires `event_id`-based dedup or an observation-ID-guarded append.

**Correlation buffers:**
- `HSET` for individual fields is idempotent for the same field values.
- Risk: if the same event triggers both field-set and status-change logic, replaying could re-trigger a status transition. Guard status transitions with conditional checks (e.g. only transition `partial → complete` if both sides' markers are present).

**Status:** PROPOSED.

### 9a.9 Snapshot & Revision Boundary

#### State-to-Feature flow

```text
Raw events (from Redpanda)
        ↓
Redis / in-memory state (mutable, incrementally updated)
        ↓
Evaluation (triggered by timer, event count, or window boundary)
        ↓
Complete FeatureRecord snapshot (self-contained, immutable once emitted)
        ↓
Revision assignment
        ↓
Feature topic publication
```

#### Key invariants

1. **The Redis state itself is mutable.** It is updated incrementally as events arrive.
2. **The published FeatureRecord must be a self-contained snapshot, not a delta** (§6 — LOCKED).
3. **Duplicate delivery is handled by snapshot replacement:** a consumer that receives the same or an older snapshot for the same `(entity_key, window_start, window_end)` identity simply retains the higher-revision version.
4. **Older revisions must never overwrite newer state** (§6).

#### Revision assignment

The `revision` field on each FeatureRecord must provide a total ordering for snapshots of the same logical identity.

**Candidate mechanisms (PROPOSED / OPEN):**

- **`computed_at` as revision proxy:** Use the emission wall-clock timestamp. Simple, but unsafe if multiple workers can concurrently emit snapshots for the same entity and clock skew exists.
- **Redis-native monotonic counter:** `INCR irochi:revision:<entity_type>:<entity_key>` — provides a strict monotonic sequence per entity. More complex, adds one Redis round-trip per snapshot emission.
- **Hybrid:** Use `computed_at` as the primary ordering and fall back to a Redis counter only for entities that can be concurrently evaluated by multiple workers.

**Required invariant:** For any two snapshots S1 and S2 with the same `(entity_key, window_start, window_end)`, if S2 was computed from strictly more recent state than S1, then `S2.revision > S1.revision`.

**Status:** The invariant is LOCKED (inherited from §6). The specific revision mechanism remains OPEN.

### 9a.10 In-Memory vs Redis Policy

#### When in-memory state is allowed

A feature's intermediate state **may** be kept in-memory (Python data structures, River state, etc.) when **all** of the following hold:

1. **Partition locality is sufficient:** Under the current `src_ip` partition key, all events for the same source IP land on the same Redpanda partition. A Feature Processing worker assigned to that partition can safely accumulate source-entity state locally.
2. **Cross-worker visibility is not required:** No other worker needs to read or update this state.
3. **State loss on worker restart is acceptable** or the state can be **reconstructed from Redpanda replay** within the raw retention horizon.
4. **The state does not need to survive consumer-group rebalancing** without reconstruction.

#### When Redis is required

Redis state is required when **any** of the following hold:

1. **Entity type lacks partition locality:** Destination-entity state (DDoS) is scattered across source-keyed partitions. Pair-entity state is not guaranteed locality. Connection correlation spans topics.
2. **Cross-worker sharing is necessary for correctness:** Multiple workers may process events relevant to the same entity.
3. **State must survive worker restart** and cannot be fully reconstructed from Redpanda replay (e.g. window horizon exceeds 24h retention, or reconstruction cost is prohibitive).
4. **High-value state** where loss would silently degrade detection quality.

#### Current entity-type guidance

| Entity type | Default locality | Redis required? | Reasoning |
|---|---|---|---|
| Source | Good under `src_ip` key | Conditional — in-memory viable when partition locality guarantees single-worker ownership; Redis when shared/recovery requirements exist | Under current `src_ip` partitioning, source events land on the same partition; a single assigned worker can maintain state locally |
| Destination | None under `src_ip` key | Required under current partitioning | Destination aggregation spans many source-keyed partitions; no single worker sees all events for one destination |
| Pair | Not guaranteed under `src_ip` key | Required under current partitioning | Pair locality is not guaranteed when raw events are source-keyed; both sides of a pair may land on different partitions |
| Connection (correlation) | Spans topics | Required | `connection` and `tls` records can arrive through different topics/partitions; shared state is needed for the join |

These Redis requirements are consequences of the current partitioning model, not absolute architectural mandates. If the partitioning model changes, the Redis requirement should be re-evaluated.

**Status:** PROPOSED.

### 9a.11 Keyspace Governance

#### Structural key patterns

| State class | Key pattern | Structural components |
|---|---|---|
| Sliding bucket | `irochi:feature:<entity_type>:<entity_key>:bucket:<time_bucket>` | `entity_type` = `source` \| `destination` \| `pair`; `entity_key` = IP or pair encoding; `time_bucket` = derived from timestamp and bucket width |
| Sliding HLL | `irochi:feature:<entity_type>:<entity_key>:hll:<time_bucket>` | Same as above; separate key because HLL is a distinct data structure |
| Sliding frequency | `irochi:feature:<entity_type>:<entity_key>:freq:<time_bucket>` | Entropy-specific frequency/distribution state |
| Tumbling window | `irochi:feature:<entity_type>:<entity_key>:window:<window_id>` | `window_id` = derived from window boundaries |
| Pair Tier 1 | `irochi:feature:pair:<pair_key>:tier1` | `pair_key` = `<src_ip>\|<dst_ip>` |
| Pair Tier 2 | `irochi:feature:pair:<pair_key>:tier2` | Same pair encoding |
| Pair Tier 2 history | `irochi:feature:pair:<pair_key>:tier2:history` | Bounded observation list |
| Correlation | `irochi:feature:connection:<connection_id>:correlation` | `connection_id` from canonical event |
| Dedup marker | `irochi:dedup:<event_id>` | Optional — only if explicit event-level dedup is used |
| Revision counter | `irochi:revision:<entity_type>:<entity_key>` | Optional — only if Redis-native revision is chosen |

#### Open structural questions

- **`time_bucket` derivation:** `floor(event_timestamp / bucket_width)` is the expected derivation. Exact `bucket_width` is OPEN.
- **`window_id` derivation:** `floor(event_timestamp / window_duration)` for Tumbling windows. Exact `window_duration` is OPEN.
- **Pair key delimiter:** `|` is the current proposed delimiter; alternative delimiters or structured encoding remain implementation choices.
- **Shared vs per-domain hashes for source-keyed Sliding buckets:** Multiple source-entity features (Recon scan_rate, DNS query_frequency, Exfiltration byte_rate) could share one Hash per `source:<src_ip>:bucket:<time_bucket>` or use separate per-domain keys. Trade-off: fewer keys vs simpler per-domain reasoning. **OPEN.**

**Status:** PROPOSED.

### 9a.12 TTL / Retention Principle

No numeric TTL values are assigned. The principle is:

```text
TTL = state_lifetime + late_arrival_grace + recovery_margin
```

where:
- `state_lifetime` = the duration the state is actively maintained (window duration for Tumbling; window duration + oldest bucket age for Sliding)
- `late_arrival_grace` = buffer for events that arrive after their nominal time bucket/window due to ingestion delay or Redpanda consumer lag
- `recovery_margin` = additional buffer for worker restart and state reconstruction (where applicable)

#### Per-state-class TTL guidance

| State class | Lifetime basis | TTL principle |
|---|---|---|
| Sliding bucket | Bucket width × number of buckets in the Sliding window | `(window_duration) + late_arrival_grace` — buckets older than the window are no longer evaluated |
| Tumbling window | Window duration | `window_duration + late_arrival_grace` — after window closes and snapshot is emitted, the accumulator can expire |
| Pair Tier 1 | Observation window for gating | Shorter TTL — Tier 1 is lightweight and loss is acceptable; the pair will re-enter on next observation |
| Pair Tier 2 | Sliding window duration for periodicity | Longer TTL — Tier 2 holds higher-value state; TTL must cover the full periodicity observation horizon |
| Correlation buffer | Correlation timeout | `correlation_timeout + grace` — short-lived; if both sides haven't arrived within timeout, emit as partial and expire |
| Dedup marker | At-least-once delivery window | Must outlive the maximum expected redelivery lag; typically short |
| Revision counter | Entity lifetime | Persists as long as the entity is actively tracked; may share the entity's TTL |

Exact numeric values remain **OPEN** and benchmark/dataset-driven.

**Status:** PROPOSED (principle); OPEN (values).

### 9a.13 Hot-Key Risk

#### DDoS destination hot-key

DDoS destination state creates Redis hot-key contention during the exact high-rate conditions the feature is designed to detect: many events targeting one `dst_ip` simultaneously.

**Primary mitigation (LOCKED):** Atomic per-bucket counters (`HINCRBY`). No read-modify-write pattern. Each event contributes one or more atomic increments without reading current state. This eliminates serialization contention at the application level.

**HyperLogLog updates** (`PFADD`) are also atomic and non-blocking for cardinality state.

**Residual risk:** At extremely high event rates, a single Redis Hash key for one `dst_ip` bucket could become a Redis-internal hotspot. This is a Redis-server-level concern, not an application-level serialization problem.

**Secondary mitigation (OPEN):** Logical destination-key sharding — split one destination's bucket into N sub-buckets (e.g. `irochi:feature:destination:<dst_ip>:bucket:<time_bucket>:shard:<shard_id>`) and aggregate at evaluation time. This adds read complexity and should only be introduced if benchmarking shows that atomic increments on a single key are still a bottleneck.

**Sharding is not locked and must not be introduced without benchmark evidence.**

**Status:** Atomic counter baseline is LOCKED. Sharding remains OPEN.

### 9a.14 State Lifecycle

#### Tumbling window lifecycle

```text
Window opens (first event in the window interval)
        ↓
Accumulate (HINCRBY / PFADD for each event in the window)
        ↓
Window closes (window_end reached)
        ↓
Evaluate (read accumulated state, compute feature values)
        ↓
Emit snapshot (publish FeatureRecord with complete window data)
        ↓
Expire (TTL removes the window-instance key after grace period)
```

#### Sliding window lifecycle

```text
Event arrives
        ↓
Determine time bucket
        ↓
Update bucket (HINCRBY / PFADD — atomic, append-only within bucket)
        ↓
Evaluation trigger (timer or event-driven)
        ↓
Aggregate relevant buckets covering [now - window_duration, now]
        ↓
Compute feature values from aggregated state
        ↓
Emit snapshot (publish FeatureRecord)
        ↓
Old buckets expire (TTL removes buckets outside the window + grace)
```

Sliding windows are continuously recomputed. There is no single "close" event — the window slides forward as time advances and old buckets fall outside the window range.

#### Tier 1 pair state lifecycle

```text
First observation of (src_ip, dst_ip) pair
        ↓
Create Tier 1 state (count=1, first_seen, last_seen)
        ↓
Subsequent observations → increment count, update last_seen
        ↓
Promotion check: count >= threshold?
   ├── NO → continue in Tier 1 (no feature output)
   └── YES → promote to Tier 2
        ↓
Tier 1 state may be retained for bookkeeping or expired
```

#### Tier 2 pair state lifecycle

```text
Promotion from Tier 1
        ↓
Create Tier 2 state (summary fields, empty observation history)
        ↓
Subsequent observations → compute inter-arrival, update summary + history
        ↓
Evaluation trigger
        ↓
Compute periodicity/variance/regularity from stored state
        ↓
Emit beaconing FeatureRecord snapshot
        ↓
Continue accumulating (Sliding — no single close event)
        ↓
Eviction (if pair becomes inactive beyond TTL — pair state expires)
```

#### Correlation lifecycle

```text
First side arrives (connection or tls event)
        ↓
Create correlation buffer: correlation_status = "partial"
        ↓
Second side arrives?
   ├── YES → set correlation_status = "complete", emit snapshot
   └── NO (timeout) → emit snapshot with correlation_status = "partial"
        ↓
Buffer expires (TTL)
        ↓
Late arrival after timeout/expiry?
   → Create new buffer or amend existing: correlation_status = "late_amendment"
   → Emit new snapshot with higher revision
```

**Status:** PROPOSED.

### 9a.15 Recovery / Rebuild

#### After Feature Processing restart

When a Feature Processing worker restarts, its in-memory state is lost. Recovery depends on the state class:

**State recoverable from Redpanda replay:**
- Source-entity state for windows shorter than the 24h raw-retention horizon can be fully reconstructed by replaying raw events from Redpanda.
- This is the expected recovery path for most source-keyed in-memory state.

**State recoverable from Redis:**
- Redis-backed state (destination, pair, correlation) survives worker restart because it is external to the worker process.
- On restart, the worker resumes processing from its last committed Redpanda consumer offset and continues updating existing Redis state.

**State not fully recoverable:**
- If a window's duration approaches or exceeds the 24h raw-retention horizon, replay cannot reconstruct the full window. The replayed portion produces a partial window that may undercount.
- **Mitigation (PROPOSED):** For long-window state classes, periodic Redis state checkpointing — persist a snapshot of the in-progress state to Redis at regular intervals so that restart recovery starts from the checkpoint rather than from an empty state.
- Whether this is needed depends on the final window durations, which remain OPEN.

**Correlation buffer recovery:**
- Correlation buffers are short-lived and stored in Redis. They survive worker restart.
- If a correlation buffer has expired by the time the worker restarts, the correlation is lost. For short correlation timeouts, this is acceptable — the events are still in Redpanda and a new correlation attempt can be made.

**No new persistence system is created.** Recovery relies on:
1. Redpanda replay (primary for in-memory state)
2. Shared hot state maintained in Redis (for Redis-backed state). Redis remains hot state per BD-004, not the durable source of truth; PostgreSQL remains the durable truth for alerts per BD-003.
3. Periodic checkpointing to Redis (proposed for long-window in-memory state).

**Status:** PROPOSED.

### 9a Status

**PROPOSED.** All state shapes, data structures, key patterns, and evaluation approaches described in this section are proposed structural baselines. They may be refined during implementation. Items explicitly marked OPEN require benchmark/dataset-driven resolution or depend on upstream decisions not yet made.


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

The atomic counter strategy (`INCR`/`HINCRBY` against time-bucketed counters, no read-modify-write) is now **LOCKED** (Approval provenance: AR-01) as the baseline approach. Detailed state model, key shapes, and evaluation flow are defined in §9a.2. Logical destination-key sharding remains OPEN as a future benchmark-driven optimization (§9a.13).

### 16.2 Pair-state cardinality control

The Tier 1 / Tier 2 split (gating vs feature-producing) is now **LOCKED** (Approval provenance: AR-01) in terms of existence and roles. Detailed state model, key shapes, promotion flow, and eviction considerations are defined in §9a.5. Promotion thresholds, eviction policy, and memory budget remain OPEN.

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

- [ ] Mechanism for `repeated-destination behaviour` (§4/§8) — no Redis state modeled until semantics are resolved
- [ ] Confirm semantics of `windowed transfer volume` / `large-transfer indicators` — per-connection vs. session/bounded aggregate (§4/§8) — no Redis state modeled until resolved
- [ ] Window durations per detector domain (§8) — pending benchmark/dataset review
- [ ] Bucket widths for Sliding windows (§8/§9a) — pending benchmark/dataset review
- [ ] Session inactivity gaps (§8) — pending benchmark/dataset review
- [ ] Feature-topic retention/cleanup policy: `delete` vs. `compact` (§11)
- [ ] Long-window vs. 24h raw-retention recovery risk (§8/§9a.15) — whether Feature Processing needs periodic state checkpointing
- [ ] Shape of provenance for high-volume windowed records (§18)
- [ ] Exact TTL values for all Redis state classes (§9a.12) — principle defined, numeric values pending benchmark
- [ ] Exact retry/backoff behaviour for the feature DLQ
- [ ] DDoS destination-key sharding (§9a.13) — only if benchmarking proves atomic counters are insufficient
- [ ] Pair-state promotion threshold (§9a.5) — exact value TBD
- [ ] Pair-state eviction policy and memory budget (§9a.5)
- [ ] Pair-state Tier 2 observation history max length (§9a.5)
- [ ] DDoS `source_ip_entropy` frequency/distribution state implementation (§9a.2) — HLL alone insufficient for entropy; exact approach OPEN
- [ ] HyperLogLog vs exact-set final selection for distinct-count features (§9a.2/§9a.3) — HLL is proposed baseline
- [ ] Shared vs per-domain source-keyed Sliding Hash keys (§9a.11)
- [ ] Feature Processing internal scaling model (§16.3)
- [ ] Snapshot `revision` monotonicity implementation (§9a.9) — invariant defined, mechanism OPEN
- [ ] Correlation timeout value (§9a.7)
- [ ] Dedup mechanism for non-idempotent counter updates (§9a.8) — event_id-based dedup vs idempotent construction
- [x] Redpanda raw-topic partition key — **LOCKED** as uniform `src_ip` (§7), recorded in Redpanda v5 §4 and BD-009
- [x] Redis state shapes per detector domain — **PROPOSED** structural baselines defined (§9a)
- [x] Redis keyspace convention — **PROPOSED** key patterns defined (§9a.11)

**OUT OF SCOPE FOR MVP:**

- UDP amplification/asymmetry metrics (§4) — capture-point / sensor-placement semantics not resolved; not required for MVP

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
- [x] Feature-level window-mechanism assignments resolved in v6 are reflected consistently in §4 (table) and §8 (prose).
- [ ] No window duration, retention number, or TTL value has been hard-coded without a benchmark basis.
- [x] The snapshot-not-delta rule (§6) is LOCKED as a processing invariant.
- [ ] Redis keyspace convention (§9/§9a.11) is either accepted or explicitly revised before implementation begins.
- [x] Redis state inventory (§9a.1) covers all resolved stateful features from §4.
- [x] Redis state model distinguishes distinct-count (HLL) from entropy (frequency/distribution) for `source_ip_entropy`.
- [x] The four foundational items locked in v7 (Task 16a) are reflected in §23.
- [ ] No Redis state has been created for features with unresolved semantics (`repeated-destination behaviour`, exfiltration transfer-volume/large-transfer indicators).
- [ ] In-memory vs Redis boundary (§9a.10) is consistent with the partition-key and entity-type analysis.

---

## 23. Decision Status Summary

| Design Item | Status |
|---|---|
| Three-mechanism typology (enrichment / windowed / correlation) | **PROPOSED** |
| Four-entity typology (source / destination / pair / connection) | **PROPOSED** |
| Detector-to-entity-and-mechanism mapping (§4) | **PROPOSED (with resolved rows)** |
| Feature record envelope shape | **PROPOSED** |
| Snapshot-not-delta rule (§6) | **LOCKED PROCESSING INVARIANT** (Approval provenance: AR-01) — upgraded in v7; required for state-to-feature boundary (§9a.9); consistent across all revisions since introduction |
| Raw-topic partition key = uniform `src_ip` | **LOCKED — inherited from Redpanda v5 §4 / BD-009** |
| Window-type taxonomy (Tumbling/Sliding/Session) | **LOCKED** |
| Feature-level window mapping | **PROPOSED (individual rows resolved; see §4/§8)** |
| DDoS atomic counter strategy (INCR/HINCRBY baseline) | **LOCKED** (Approval provenance: AR-01) — upgraded in v7; required for DDoS destination state model (§9a.2/§9a.13); sharding remains OPEN as optimization |
| Directional pair key `(src_ip, dst_ip)`, not canonicalized (§3) | **LOCKED** (Approval provenance: AR-01) — added in v7; required for Tier 1/Tier 2 key shapes (§9a.5); unchanged since introduction |
| Pair-state Tier 1/Tier 2 split: existence and roles | **LOCKED** (Approval provenance: AR-01) — split from prior "Pair-state two-tier tracking" row in v7; Tier 1 = gating only, Tier 2 = feature-producing; required for §9a.5 |
| Pair-state promotion threshold, eviction policy, memory budget | **OPEN** — split from prior "Pair-state two-tier tracking" row; these operational parameters remain explicitly unresolved |
| Redis state shapes per detector domain (§9a) | **PROPOSED** — structural baselines for all resolved stateful features |
| Redis keyspace convention (§9/§9a.11) | **PROPOSED** — key patterns defined; structural, not locked |
| Redis TTL values | **OPEN — principle defined (§9a.12), numeric values pending benchmark** |
| In-memory vs Redis boundary (§9a.10) | **PROPOSED** — policy defined; deployment-time decision |
| HyperLogLog vs exact-set for distinct-count | **PROPOSED (HLL baseline) / OPEN (final selection)** |
| DDoS `source_ip_entropy` frequency/distribution state | **PROPOSED / OPEN** — minimum state requirements identified; implementation choice OPEN |
| DDoS destination-key sharding | **OPEN — benchmark-driven optimization only** |
| Dedup mechanism for counter updates (§9a.8) | **PROPOSED / OPEN** |
| Revision monotonicity mechanism (§9a.9) | **PROPOSED / OPEN** — invariant is LOCKED (§6); specific mechanism OPEN |
| Correlation timeout | **OPEN** |
| State lifecycle model (§9a.14) | **PROPOSED** |
| Recovery / rebuild strategy (§9a.15) | **PROPOSED** |
| UDP amplification/asymmetry metrics | **OUT OF SCOPE FOR MVP** |
| `repeated-destination behaviour` mechanism | **OPEN** |
| Exfiltration transfer-volume/large-transfer semantics | **OPEN** |
| Window durations | **OPEN — pending benchmark** |
| Bucket widths | **OPEN — pending benchmark** |
| Session inactivity gaps | **OPEN — pending benchmark** |
| One feature topic per detector domain | **PROPOSED** |
| Feature-topic partition key = entity key | **PROPOSED** |
| Feature-topic retention: `delete` vs `compact` | **OPEN** |
| Per-detector consumer groups | **PROPOSED** |
| At-least-once delivery for feature records | **PROPOSED** |
| Shared feature DLQ | **PROPOSED** |
| JSON serialization | **PROPOSED** |
| Generic `provenance` hook | **OPEN** |
| `correlation_status` | **PROPOSED / OPEN** |
| Feature Processing internal scaling | **OPEN** |

Items marked LOCKED in this table have explicit project-lead approval (AR-01). PROPOSED items are structural baselines subject to review. OPEN items require benchmark/dataset resolution or depend on upstream decisions not yet made.

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

### Design-chain discipline

Detector I/O design may begin using the approved Feature/Window envelope shape (§5) and the locked window taxonomy (§8). However, detector-specific payload details depend on feature mappings that remain PROPOSED or OPEN in §4 (particularly `repeated-destination behaviour` and exfiltration transfer-volume semantics), and the provenance question (§18) must be explicitly resolved before Alert Schema design begins to ensure alert explainability. Do not treat all downstream payloads as finalized.

---

## 25. Final Status

**DRAFT v7 — Redis state modeling pass complete.**

This revision adds §9a (Redis State Model) covering state inventory, per-detector state shapes, deduplication/atomicity, snapshot/revision boundary, in-memory vs Redis policy, keyspace governance, TTL principles, hot-key risk, state lifecycle, and recovery/rebuild.

Four foundational items were explicitly locked with project-lead approval (AR-01):
1. Snapshot-not-delta rule → **LOCKED PROCESSING INVARIANT**
2. DDoS atomic counter strategy (INCR/HINCRBY baseline) → **LOCKED**
3. Directional pair key `(src_ip, dst_ip)`, not canonicalized → **LOCKED**
4. Tier 1/Tier 2 pair-state split (existence and roles) → **LOCKED**

Window-mechanism taxonomy remains **LOCKED** (Tumbling / Sliding / Session). Redis state shapes are **PROPOSED** structural baselines. Remaining items (`repeated-destination behaviour`, exfiltration transfer-volume/large-transfer semantics, all durations/widths/gaps/TTLs, entropy implementation, promotion thresholds, eviction policy, memory budgets, HLL vs exact-set final selection, correlation timeout, revision mechanism) are explicitly **OPEN**. UDP amplification/asymmetry metrics remain **OUT OF SCOPE FOR MVP**.

No Feature/Window topics, Redis keys, or consumers should be implemented in code from this document until the proposed design is explicitly reviewed and approved.
