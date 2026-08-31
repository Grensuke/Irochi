# SIH26145 — DETECTOR INPUT / OUTPUT CONTRACT (DRAFT v1)

> **Status:** DRAFT — structural contract for review; individual section statuses vary (see §19). Requires project-lead / team review before promotion to `_FINAL`.
>
> **Continues from:** `docs/architecture/FEATURE_WINDOW_SCHEMA_DRAFT_v7.md`, `docs/architecture/SIH26145_CANONICAL_ARCHITECTURE_CHECKPOINT_FINAL.md` (§11, §12, §14, §15, §17, §18), and `docs/architecture/REDPANDA_TOPICS_DRAFT_v5.md`.
>
> **Scope:** This document defines the **structural contract** between Feature/Window processing and the Alert Engine. It specifies DetectorInput (what detectors receive), DetectorOutput (what detectors produce), feature grouping identity, partial-input behaviour, versioning/revision, and threat-type mapping. It does **not** finalize Alert Schema, PostgreSQL Schema, ML model selection, or the final API contract — those remain later design steps.

---

## 1. Design Inputs and Guardrails

This contract sits in the design chain:

```text
Canonical Event Schema
        ↓
Redpanda Topics (v5)
        ↓
Feature / Window Schema (v7)
        ↓
Detector Input / Output Contract  ← THIS DOCUMENT
        ↓
Alert Schema
        ↓
PostgreSQL Schema
        ↓
Final API Contract
```

### Inherited constraints

**LOCKED (explicit project-lead approval):**

- Snapshot-not-delta processing invariant (Feature/Window §6)
- Raw partition key = `src_ip` (BD-009)
- Window taxonomy: Tumbling / Sliding / Session (Feature/Window §8)
- Raw-vs-derived boundary (Architecture §5)
- Alert write ordering: PostgreSQL INSERT → AWAIT COMMIT → Redis Pub/Sub (Architecture §19)
- 5 detectors are logical modules, not microservices (Architecture §11)
- DDoS atomic counter strategy: INCR/HINCRBY baseline (Feature/Window §9a)
- Directional pair key `(src_ip, dst_ip)`, not canonicalized (Feature/Window §3)
- Tier 1 / Tier 2 pair-state split: existence and roles (Feature/Window §9a.5)

**Inherited / not to be altered in this pass (BD-008 status is Active, not Locked):**

- 5 canonical detector IDs — `ddos_detector`, `recon_detector`, `dns_dga_tunnel_detector`, `tls_c2_detector`, `exfiltration_detector`
- 6 threat types — `volumetric_ddos`, `c2_beaconing`, `dga_dns_tunnel`, `encrypted_malware`, `recon_portscan`, `data_exfiltration`
- detector_id ≠ threat_type (one detector may emit multiple threat classes)

> BD-008 says these values are "not yet formally locked in the final API contract but are used consistently across the dummy backend." This document inherits and uses them but does not promote them to LOCKED.

**PROPOSED (inherited from Feature/Window v7):**

- FeatureRecord envelope shape (Feature/Window §5)
- Redis state shapes per detector domain (Feature/Window §9a)

### What this document does NOT finalize

- Alert Schema fields or structure
- PostgreSQL schema
- ML model selection or training pipeline
- Exact detector/model version format
- Confidence/score numerical semantics
- Exact evidence structure
- Batching/invocation transport mechanism
- Final API contract
- Unresolved upstream feature semantics (`repeated-destination behaviour`, exfiltration transfer-volume/large-transfer)
- UDP amplification/asymmetry — OUT OF SCOPE FOR MVP

### Status

**PROPOSED.** The design inputs are inherited; this section documents their provenance.

---

## 2. Detector Taxonomy

### Five detector modules

| detector_id | Detector Module | Capability Domain | Primary Entity Types |
|---|---|---|---|
| `ddos_detector` | DDoS Detector | Volumetric / protocol flood detection | Destination |
| `recon_detector` | Recon Detector | Reconnaissance / port scanning detection | Source |
| `dns_dga_tunnel_detector` | DNS/DGA/DNS-Tunneling Detector | DGA detection, DNS tunneling detection | Source (windowed and enrichment) |
| `tls_c2_detector` | TLS/C2 Detector | Encrypted-session malware, C2 beaconing | Connection (enrichment and correlation), Pair (beaconing) |
| `exfiltration_detector` | Exfiltration Detector | Data exfiltration detection | Source |

These are logically distinct modules, **not** separate microservices (Architecture §11).

### Detector → Threat-type mapping

A detector may emit **one or more** threat types. `detector_id ≠ threat_type`.

| detector_id | Threat type(s) it may emit |
|---|---|
| `ddos_detector` | `volumetric_ddos` |
| `recon_detector` | `recon_portscan` |
| `dns_dga_tunnel_detector` | `dga_dns_tunnel` |
| `tls_c2_detector` | `c2_beaconing`, `encrypted_malware` |
| `exfiltration_detector` | `data_exfiltration` |

Note: `tls_c2_detector` emits two distinct threat types — `encrypted_malware` (JA3 blacklist match evidence) and `c2_beaconing` (periodic connection pattern evidence). These represent different threat interpretations from the same detector module.

### Detector → Input feature classes

| detector_id | Input Feature Classes | Mechanisms |
|---|---|---|
| `ddos_detector` | `packet_rate`, `byte_rate`, `syn_ratio`, `source_ip_entropy` | Windowed (Sliding) |
| `recon_detector` | `unique_destination_ports`, `unique_destination_hosts`, `connection_fan_out`, `scan_rate` | Windowed (Tumbling + Sliding) |
| `dns_dga_tunnel_detector` | `domain_entropy`, `query_length`, `n_gram_score`, label-length statistics, `query_frequency`, record-type distribution | Enrichment + Windowed (Sliding + Tumbling) |
| `tls_c2_detector` | `ja3_blacklist_match`, connection↔tls correlation, `inter_arrival_time`, `beacon_periodicity`, periodicity variance, regularity, connection frequency | Enrichment + Correlation + Windowed (Sliding) |
| `exfiltration_detector` | `outbound_inbound_ratio`, `byte_rate` | Windowed (Sliding) |

**Heterogeneous feature mechanisms are explicitly permitted.** `dns_dga_tunnel_detector`, `tls_c2_detector`, and `recon_detector` all consume features from multiple mechanisms and/or differently-timed windows. The contract must support this without forcing a single mechanism/window shape onto all inputs.

### Status

**PROPOSED.** Detector identities and threat types are inherited from BD-008 (Active). The feature-class mapping is derived from Feature/Window v7 §4.

---

## 3. DetectorInput Envelope

A DetectorInput represents **one routed FeatureRecord** — it carries the upstream FeatureRecord's envelope fields plus routing context (`input_id` and `detector_id`).

A multi-FeatureRecord detector evaluation (e.g. Recon consuming both Tumbling breadth and Sliding scan_rate snapshots) consumes a **set** of DetectorInputs, grouped by the base grouping identity and temporal association policy defined in §11. Each DetectorInput in the set corresponds to exactly one source FeatureRecord.

### Envelope fields

| Field | Type | Required | Source | Description |
|---|---|---|---|---|
| `input_id` | UUID/string | Yes | Generated by routing layer | Unique identifier for this detector input instance |
| `detector_id` | enum | Yes | Derived from `detector_domain` | Target detector: `ddos_detector`, `recon_detector`, `dns_dga_tunnel_detector`, `tls_c2_detector`, or `exfiltration_detector` |
| `feature_id` | UUID/string | Yes | From FeatureRecord | Unique identifier of the source FeatureRecord |
| `mechanism` | enum | Yes | From FeatureRecord | `enrichment`, `windowed`, or `correlation` |
| `detector_domain` | enum | Yes | From FeatureRecord | `ddos`, `recon`, `dns`, `tls_c2`, or `exfil` |
| `entity_type` | enum | Yes | From FeatureRecord | `source`, `destination`, `pair`, or `connection` |
| `entity_key` | string | Yes | From FeatureRecord | The actual key value |
| `window_type` | enum | Conditional | From FeatureRecord | `tumbling`, `sliding`, or `session`; present only for `windowed` records |
| `window_start` | int64 | Conditional | From FeatureRecord | Epoch microseconds; present only for `windowed` records |
| `window_end` | int64 | Conditional | From FeatureRecord | Epoch microseconds; present only for `windowed` records |
| `computed_at` | int64 | Yes | From FeatureRecord | Time Feature Processing emitted the record |
| `schema_version` | string | Yes | From FeatureRecord | Version of the feature-record contract |
| `revision` | int | Yes | From FeatureRecord | Monotonically increasing snapshot revision for the same entity/window |
| `correlation_status` | enum | Conditional | From FeatureRecord | `partial`, `complete`, or `late_amendment`; present only for `correlation` records |
| `provenance` | object | Optional | From FeatureRecord | References to contributing raw events; exact shape remains open |
| `payload` | object | Yes | From FeatureRecord | Typed feature payload (see §4) |

### Design rationale

- The DetectorInput does **not** duplicate FeatureRecord fields — it passes them through from the source FeatureRecord with the addition of `input_id` and `detector_id`.
- The `detector_id` is derived from `detector_domain` using the mapping defined in Feature/Window v7 §5: `ddos` → `ddos_detector`, `recon` → `recon_detector`, `dns` → `dns_dga_tunnel_detector`, `tls_c2` → `tls_c2_detector`, `exfil` → `exfiltration_detector`.
- A detector receives **self-contained** inputs — it does not need to reconstruct features from raw events.
- `window_type`, `window_start`, `window_end`, and `correlation_status` are conditional because enrichment records genuinely do not carry window fields. (AR-02: `entity_type` and `entity_key` are explicitly required for all records, including enrichment, to preserve logical entity context).

### Status

**PROPOSED.**

---

## 4. Payload Strategy

**Decision: Option C — Common envelope + typed detector-capability payloads.**

This matches the established pattern in both the Canonical Event Schema (envelope + typed payload) and the FeatureRecord (envelope + typed payload).

```text
DetectorInput
├── Envelope (§3 fields)
└── Typed Payload
    ├── DdosFeaturePayload
    ├── ReconFeaturePayload
    ├── DnsFeaturePayload        (carries both enrichment and windowed fields)
    ├── TlsC2FeaturePayload      (carries enrichment, correlation, and windowed fields)
    └── ExfilFeaturePayload
```

The typed payload is **the same typed payload** defined by the FeatureRecord in Feature/Window v7 §5. The DetectorInput does not create a second layer of payload typing — it passes through the FeatureRecord's typed payload directly.

### Why not Option A (generic feature map)

A generic `Dict[str, Any]` feature map loses type safety and makes it impossible for a detector to validate its expected inputs at the contract level. It also obscures the enrichment/windowed/correlation mechanism distinction.

### Why not Option B (detector-specific payloads)

Creating new detector-specific payload types that are separate from FeatureRecord payloads would duplicate the feature definitions and create a synchronization burden between Feature/Window and Detector I/O.

### Status

**PROPOSED.**

---

## 5. Detector Contract Table

| | `ddos_detector` | `recon_detector` | `dns_dga_tunnel_detector` | `tls_c2_detector` | `exfiltration_detector` |
|---|---|---|---|---|---|
| **Capability** | Volumetric / protocol flood detection | Reconnaissance / port scanning | DGA detection, DNS tunneling | Encrypted-session malware, C2 beaconing | Data exfiltration |
| **Accepted Feature Domains** | `ddos` | `recon` | `dns` | `tls_c2` | `exfil` |
| **Accepted Mechanisms** | Windowed | Windowed | Enrichment, Windowed | Enrichment, Correlation, Windowed | Windowed |
| **Accepted Entity Types** | Destination | Source | Source (windowed and enrichment) | Connection (enrichment and correlation), Pair (beaconing) | Source |
| **Required Features** | `packet_rate`, `byte_rate`, `syn_ratio`, `source_ip_entropy` | `unique_destination_ports`, `unique_destination_hosts`, `connection_fan_out`, `scan_rate` | At least one of: enrichment features OR windowed features (see §8) | At least one of: enrichment, correlation, or beaconing features (see §9) | `outbound_inbound_ratio`, `byte_rate` |
| **Optional Features** | — | — | Any feature from the other mechanism | Any feature from the other mechanisms | — |
| **Partial Input Allowed?** | Yes — with reduced capability (see §12) | Yes — Tumbling and Sliding may arrive independently (see §12) | Yes — enrichment-only or windowed-only evaluation permitted (see §12) | Yes — any single mechanism may trigger evaluation (see §12) | Yes — with reduced capability (see §12) |
| **Output** | DetectorOutput (§14) with threat_type `volumetric_ddos` | DetectorOutput (§14) with threat_type `recon_portscan` | DetectorOutput (§14) with threat_type `dga_dns_tunnel` | DetectorOutput (§14) with threat_type `c2_beaconing` or `encrypted_malware` | DetectorOutput (§14) with threat_type `data_exfiltration` |

### Status

**PROPOSED.**

---

## 6. DDoS Input Contract

### Detector identity

- **detector_id:** `ddos_detector`
- **detector_domain:** `ddos`

### Input features

| Feature | Mechanism | Entity | Window Type | Required? |
|---|---|---|---|---|
| `packet_rate` | Windowed | Destination | Sliding | Yes |
| `byte_rate` | Windowed | Destination | Sliding | Yes |
| `syn_ratio` | Windowed | Destination | Sliding | Yes |
| `source_ip_entropy` | Windowed | Destination | Sliding | Yes |

### Entity / window shape

- **Entity type:** Destination (`dst_ip`)
- **Window type:** Sliding
- **Single mechanism:** All four features arrive in the same DdosFeaturePayload snapshot from the same entity/window evaluation.

### Partial input behaviour

All four features are required for a **complete-capability** DDoS evaluation. However, they are not mandatory for every invocation — the detector may be invoked with a subset. If `source_ip_entropy` is unavailable (e.g. the entropy frequency/distribution state implementation is OPEN), the detector may operate in reduced-capability mode using only `packet_rate`, `byte_rate`, and `syn_ratio`. The DetectorOutput must indicate reduced capability in the evidence (see §12).

### Exclusions

- UDP amplification/asymmetry metrics are **OUT OF SCOPE FOR MVP**. They must not appear as required or optional inputs.

### Status

**PROPOSED.**

---

## 7. Recon Input Contract

### Detector identity

- **detector_id:** `recon_detector`
- **detector_domain:** `recon`

### Input features

| Feature | Mechanism | Entity | Window Type | Required? |
|---|---|---|---|---|
| `unique_destination_ports` | Windowed | Source | Tumbling | Yes |
| `unique_destination_hosts` | Windowed | Source | Tumbling | Yes |
| `connection_fan_out` | Windowed | Source | Tumbling | Yes |
| `scan_rate` | Windowed | Source | Sliding | Yes |

### Entity / window shape

- **Entity type:** Source (`src_ip`)
- **Window types:** Mixed — Tumbling (breadth features) and Sliding (`scan_rate`)
- **Multi-mechanism:** Tumbling breadth features and Sliding `scan_rate` use independently-timed windowing state (`window_id` vs `time_bucket` per Feature/Window §9a.3) and are emitted as **separate** FeatureRecord snapshots. The temporal association policy defined in §11 governs how these are combined into one evaluation context.

### Partial input behaviour

The Tumbling and Sliding FeatureRecords may arrive independently. A detector evaluation may proceed with:
- Tumbling-only (breadth features without scan_rate) — reduced capability
- Sliding-only (scan_rate without breadth) — reduced capability
- Both present — full capability

The detector must not substitute zero for a missing feature from a window that has not yet closed. See §12.

### Status

**PROPOSED.**

---

## 8. DNS/DGA/Tunnel Input Contract

### Detector identity

- **detector_id:** `dns_dga_tunnel_detector`
- **detector_domain:** `dns`

### Input features

| Feature | Mechanism | Entity | Window Type | Required? |
|---|---|---|---|---|
| `domain_entropy` | Enrichment | per-event | n/a | Optional (enrichment) |
| `query_length` | Enrichment | per-event | n/a | Optional (enrichment) |
| `n_gram_score` | Enrichment | per-event | n/a | Optional (enrichment) |
| label-length statistics | Enrichment | per-event | n/a | Optional (enrichment) |
| `query_frequency` | Windowed | Source | Sliding | Optional (windowed) |
| record-type distribution | Windowed | Source | Tumbling | Optional (windowed) |

### Entity / window shape

- **Entity types:** Source (enrichment and windowed)
- **Window types:** n/a (enrichment — no temporal window fields), Sliding (`query_frequency`), Tumbling (record-type distribution)
- **Heterogeneous:** This detector consumes enrichment features (per DNS query, no window) and windowed features (aggregated over source). The temporal association between enrichment and windowed records is governed by §11.

### Partial input behaviour

This detector explicitly supports heterogeneous partial inputs:
- **Enrichment-only:** Evaluate DGA characteristics from a single DNS query's enrichment features. This is a per-event evaluation without windowed context.
- **Windowed-only:** Evaluate DNS tunneling behaviour from windowed source-level aggregates without per-query enrichment.
- **Combined:** Both enrichment and windowed features available — full capability.

At least one feature from either mechanism must be present. See §12.

### Status

**PROPOSED.**

---

## 9. TLS/C2 Input Contract

### Detector identity

- **detector_id:** `tls_c2_detector`
- **detector_domain:** `tls_c2`

### Input features

| Feature | Mechanism | Entity | Window Type | Required? |
|---|---|---|---|---|
| `ja3_blacklist_match` | Enrichment | per-event | n/a | Optional (enrichment) |
| Connection↔TLS correlation fields | Correlation | Connection | n/a | Optional (correlation) |
| `correlation_status` | Correlation | Connection | n/a | Conditional (present when correlation input is present) |
| `inter_arrival_time` | Windowed | Pair | Sliding | Optional (beaconing) |
| `beacon_periodicity` | Windowed | Pair | Sliding | Optional (beaconing) |
| periodicity variance | Windowed | Pair | Sliding | Optional (beaconing) |
| regularity | Windowed | Pair | Sliding | Optional (beaconing) |
| connection frequency | Windowed | Pair | Sliding | Optional (beaconing) |

### Entity / window shape

- **Entity types:** Connection (enrichment and correlation), Pair (beaconing)
- **Window types:** n/a (enrichment/correlation — no temporal window fields), Sliding (beaconing)
- **Heterogeneous:** This detector consumes features from **three distinct mechanisms** with **three different entity types**. The temporal association between these inputs is governed by §11.

### Partial input behaviour

This detector explicitly supports evaluation from any single mechanism:
- **Enrichment-only:** JA3 blacklist match → `encrypted_malware` threat type (medium-confidence supporting signal per Architecture §12.4)
- **Correlation-only:** Connection↔TLS correlated fields → supplementary evidence (correlation_status may be `partial`)
- **Beaconing-only:** Pair-level periodicity features → `c2_beaconing` threat type
- **Combined:** Multiple mechanisms present → increased confidence, potentially multiple threat types emitted

The `repeated-destination behaviour` feature remains **OPEN** upstream (Feature/Window §4). It must not appear as a required or optional input until its semantics are resolved.

### Status

**PROPOSED.**

---

## 10. Exfiltration Input Contract

### Detector identity

- **detector_id:** `exfiltration_detector`
- **detector_domain:** `exfil`

### Input features

| Feature | Mechanism | Entity | Window Type | Required? |
|---|---|---|---|---|
| `outbound_inbound_ratio` | Windowed | Source | Sliding | Yes |
| `byte_rate` | Windowed | Source | Sliding | Yes |

### Entity / window shape

- **Entity type:** Source (`src_ip`)
- **Window type:** Sliding
- **Single mechanism:** Both features arrive in the same ExfilFeaturePayload snapshot.

### Partial input behaviour

Both features are required for a **complete-capability** exfiltration evaluation. However, they are not mandatory for every invocation — the detector may be invoked with a subset and operate in reduced-capability mode. See §12.

### Exclusions

The following features remain **OPEN** upstream (Feature/Window §4) and must not be made required or optional inputs:
- `windowed transfer volume`
- `large-transfer indicators`

### Status

**PROPOSED.**

---

## 11. Feature Grouping / Evaluation Identity

### The grouping problem

A detector may consume features from multiple FeatureRecords that use different mechanisms, different window types, or different entity types. This section defines how multiple FeatureRecords become one detector evaluation context.

### Base grouping identity

```text
base_grouping_identity = (detector_id, entity_key)
```

Where:
- **`detector_id`** — which detector
- **`entity_key`** — the primary entity being evaluated

This is a **base grouping identity**, not a complete evaluation identity. It identifies *which entity a detector is evaluating* but does not by itself distinguish separate evaluations of the same entity at different times. Temporal/evaluation association — determining which specific FeatureRecord snapshots constitute one evaluation instance — remains a necessary additional concern addressed in the temporal association policy below.

| detector_id | entity_key |
|---|---|
| `ddos_detector` | `dst_ip` |
| `recon_detector` | `src_ip` |
| `dns_dga_tunnel_detector` | `src_ip` |
| `tls_c2_detector` | varies — `connection_id` (enrichment and correlation), `src_ip\|dst_ip` (pair/beaconing) |
| `exfiltration_detector` | `src_ip` |

### Why `evaluation_window` is not part of the base grouping identity

The base grouping identity deliberately excludes `evaluation_window` because:

1. **Enrichment-mechanism inputs carry no window fields at all** (Feature/Window §2). Forcing `evaluation_window` into the identity would require fabricating a fake window onto enrichment records — the exact failure mode §2 warns against.
2. **Some detectors consume features from differently-timed windows** (Recon: Tumbling + Sliding; DNS: Sliding + Tumbling). These arrive as separate snapshots with independent timing. The base identity identifies the entity; temporal association is a separate concern addressed below.

However, temporal/evaluation association is still necessary to distinguish separate evaluations of the same entity. The base identity alone cannot determine *which* Tumbling snapshot pairs with *which* Sliding snapshot for the same `src_ip`. This pairing is the responsibility of the temporal association policy.

### Temporal association policy for multi-mechanism detectors

Three detectors consume features from multiple mechanisms or differently-timed windows. In each case, the detector must associate records from different mechanisms into one evaluation context for the same entity.

**Affected detectors:**

- **`recon_detector`** — Tumbling breadth features (`unique_destination_ports`, `unique_destination_hosts`, `connection_fan_out`) + Sliding `scan_rate`. These use independently-timed windowing state (`window_id` vs `time_bucket` per Feature/Window §9a.3) and are emitted as separate snapshots.
- **`dns_dga_tunnel_detector`** — Enrichment (per-event, no window) + Sliding `query_frequency` + Tumbling record-type distribution.
- **`tls_c2_detector`** — Enrichment (`ja3_blacklist_match`, per-event) + Correlation (connection↔tls join) + Sliding beaconing pair features.

**Candidate association approaches (OPEN):**

1. **Event-time / overlap join:** The arriving record is associated with the most recent evaluation window(s) from the other mechanism(s) whose time range overlaps. For Recon, the Tumbling snapshot and the Sliding snapshot whose time ranges overlap are associated.
2. **Accumulate-until-evaluation-trigger:** Records from the faster-cadence mechanism (or per-event enrichment) are buffered per entity and attached to the next evaluation triggered by the other mechanism.
3. **Immediate evaluation with latest state:** An arriving record triggers an immediate detector evaluation using the most recently emitted snapshot(s) from the other mechanism(s) for that entity.

The final association policy remains **OPEN** — it depends on implementation decisions about evaluation triggers (push vs pull) and latency requirements. The structural requirement is documented: the contract must support multi-mechanism input assembly per entity.

**Detectors with a single windowed mechanism** (`ddos_detector` — Sliding only, `exfiltration_detector` — Sliding only) do not need a cross-mechanism association policy. For these, the window identity from the FeatureRecord naturally distinguishes separate evaluations of the same entity, but it remains part of the FeatureRecord content rather than the base grouping identity.

### `tls_c2_detector` entity-key complexity

`tls_c2_detector` is unique in that its three input mechanisms use **different entity types**:

- Enrichment: `connection_id`
- Correlation: `connection_id`
- Beaconing: `src_ip|dst_ip` (pair key)

The evaluation context must support associating these through a shared network context (e.g. the `src_ip` that appears in all three). The exact association mechanism is **OPEN** but the structural requirement that it exists is documented.

### Status

**PROPOSED** (grouping key structure). **OPEN** (temporal association policy, `tls_c2_detector` multi-entity association mechanism).

---

## 12. Partial Input / Missing Feature Behavior

### General principle

A detector may receive partial inputs — not all expected features may be available at evaluation time. The contract defines how each case is handled structurally.

### Case table

| Case | Handling | Rationale |
|---|---|---|
| **Required feature missing** | Evaluate with reduced capability; annotate in evidence | A detector should still attempt evaluation when possible; complete rejection wastes available evidence |
| **Optional enrichment missing** | Evaluate without it; annotate absence in evidence | Enrichment is supplementary; its absence reduces confidence but does not block evaluation |
| **Correlation marked `partial`** | Accept with reduced confidence; annotate `correlation_status = partial` in evidence | Partial correlation still provides useful information (e.g. flow-level metadata without TLS fingerprint) |
| **Feature not yet available** | Defer until evaluation trigger or timeout; then evaluate with available data | Do not block indefinitely; use whatever data is available when the evaluation trigger fires |
| **Multi-FeatureRecord assembly** | Accept when minimum required set is present | For multi-mechanism detectors, at least one mechanism's features must be present |
| **Upstream OPEN feature** | Must not appear as required or optional | Features with unresolved upstream semantics cannot be required by detectors |

### Structural rules

1. **Do not substitute zero for missing values** unless the upstream semantic explicitly supports zero as a meaningful value. Missing ≠ zero.
2. **Do not silently drop partial inputs** — every evaluation must indicate which features were available and which were absent.
3. **Reduced-capability evaluations** must produce a DetectorOutput with lower confidence and evidence indicating the limitation.
4. **Invalid inputs** (e.g. schema mismatch, unknown detector_domain) produce a `decision = invalid_input` output, not silent rejection.

### Status

**PROPOSED.**

---

## 13. Versioning / Revision

### FeatureRecord revision passthrough

The DetectorInput carries the `revision` field from the source FeatureRecord. This is the monotonically increasing snapshot revision defined by Feature/Window §6 and §9a.9.

### How revisions are used

| Concern | Handling |
|---|---|
| **Stale feature rejection** | Staleness is checked **per feature's own logical identity** — i.e. within the same `(feature's entity_key, window identity)`. A revision for one feature must not be compared against a revision for a different feature. If a DetectorInput carries a `revision` lower than the most recently processed revision for the **same feature's logical identity**, it is stale and should be discarded |
| **Source feature references** | DetectorOutput includes `source_feature_references` — a list of `{feature_id, revision}` objects identifying the exact FeatureRecords that contributed to the evaluation. Each entry carries its own revision; revisions are not comparable across different feature_ids |
| **DetectorInput revision** | DetectorInput itself does not need its own revision field — the `input_id` uniquely identifies the input, and `revision` from the FeatureRecord provides per-feature ordering |
| **DetectorOutput ordering** | `evaluated_at` is a timestamp / observability field indicating when the detector completed evaluation. It is **not** guaranteed to provide authoritative ordering of DetectorOutputs (clock skew, concurrent evaluations, or reprocessing could produce non-monotonic timestamps). Authoritative output ordering remains **OPEN** |

### Idempotency boundary

- **FeatureRecord → DetectorInput:** At-least-once delivery inherited from Redpanda. Duplicate FeatureRecords produce duplicate DetectorInputs. The detector must handle this through revision checking or by producing idempotent outputs.
- **DetectorOutput → Alert Engine:** The Alert Engine is responsible for deduplication at the alert level. DetectorOutput is the detector's decision; the Alert Engine decides whether it creates a new alert, updates an existing alert, or discards a duplicate.

### What remains OPEN

- Exact staleness-detection implementation (timestamp comparison, revision comparison, or both)
- Exact idempotency mechanism for multi-FeatureRecord evaluations
- Whether the routing layer should pre-filter stale inputs or let the detector handle it

### Status

**PROPOSED** (revision passthrough, source references). **OPEN** (staleness implementation, idempotency mechanism).

---

## 14. DetectorOutput Envelope

### Envelope fields

| Field | Type | Required | Description |
|---|---|---|---|
| `output_id` | UUID/string | Yes | Unique identifier for this detector output |
| `detector_id` | enum | Yes | Which detector produced this output |
| `input_id` | UUID/string | Yes | Identifies the specific DetectorInput that **triggered** this evaluation. For multi-FeatureRecord evaluations, this is the input whose arrival caused the detector to run. `source_feature_references` (below) identifies **all** FeatureRecords used |
| `entity_type` | enum | Yes | What was evaluated: `source`, `destination`, `pair`, or `connection` |
| `entity_key` | string | Yes | The evaluated entity's key |
| `evaluated_at` | int64 | Yes | Epoch microseconds when the detector completed evaluation |
| `detector_version` | string | Yes | Version of the detector logic (exact format OPEN) |
| `model_version` | string | Conditional | Version of the ML model, if applicable (exact format OPEN); omitted for rule/statistical-only detectors |
| `decision` | enum | Yes | `no_threat`, `detection`, `insufficient_data`, `invalid_input`, or `detector_error` (see §16) |
| `threat_type` | enum | Conditional | From the established taxonomy; present only when `decision = detection` |
| `confidence` | float | Conditional | [0.0, 1.0]; present only when `decision = detection` or `decision = no_threat` (numerical semantics OPEN) |
| `score` | float | Optional | Raw detector score before confidence normalization (semantics OPEN) |
| `severity_candidate` | enum | Conditional | Detector's severity suggestion: `critical`, `high`, `medium`, `low`, `info`; present when `decision = detection`. Alert Engine may override |
| `evidence` | object | Conditional | Structured evidence; present when `decision = detection` or `decision = no_threat` (see below) |
| `source_feature_references` | list | Yes | List of `{feature_id, revision}` objects identifying contributing FeatureRecords |
| `schema_version` | string | Yes | Version of the DetectorOutput contract |

### Evidence structure (PROPOSED)

```text
evidence:
  features_used:
    - feature_name: "packet_rate"
      value: 12400.5
      contribution: "high"      # qualitative contribution indicator
    - feature_name: "syn_ratio"
      value: 0.98
      contribution: "high"
    ...
  features_missing:
    - feature_name: "source_ip_entropy"
      reason: "not_yet_available"
  summary: "string — human-readable evidence summary"
```

The evidence structure must be sufficient for:
1. Alert Engine to construct analyst-facing evidence summaries
2. Downstream explainability / investigation
3. Audit trail of which features contributed to which decision

The exact evidence structure remains **PROPOSED** — it will be refined during Alert Schema design.

### Design boundaries

- **DetectorOutput is the detector's decision/result contract.** It is NOT the alert itself.
- **Alert Schema** converts DetectorOutput into an analyst-facing alert record. That conversion is a downstream design step.
- **`severity_candidate`** is the detector's suggestion. The Alert Engine owns the final severity assignment (it may consider cross-detector correlation, historical context, or analyst-defined policies).

### Status

**PROPOSED** (envelope fields, evidence baseline). **OPEN** (exact detector/model version format, confidence/score numerical semantics, exact evidence field typing).

---

## 15. Threat-Type Mapping

### Existing threat taxonomy (inherited from BD-008 / DATA_CONTRACTS.md)

| Threat Type ID | Description | Emitting Detector(s) |
|---|---|---|
| `volumetric_ddos` | Volumetric / Protocol DDoS | `ddos_detector` |
| `c2_beaconing` | Botnet C2 Beaconing | `tls_c2_detector` |
| `dga_dns_tunnel` | DGA / DNS Tunneling | `dns_dga_tunnel_detector` |
| `encrypted_malware` | Malware inside encrypted sessions | `tls_c2_detector` |
| `recon_portscan` | Reconnaissance / Port Scanning | `recon_detector` |
| `data_exfiltration` | Data Exfiltration | `exfiltration_detector` |

### Mapping rules

1. **`detector_id ≠ threat_type`** — A detector may emit one or more threat types. Specifically, `tls_c2_detector` may emit either `c2_beaconing` or `encrypted_malware` depending on which evidence triggered the detection.
2. **No new threat types are created** by this document. The taxonomy is inherited and maintained in `DATA_CONTRACTS.md`.
3. **A single DetectorOutput carries exactly one `threat_type`** when `decision = detection`. If a detector evaluation identifies evidence for multiple threat types (e.g. `tls_c2_detector` finds both JA3 blacklist match and beaconing pattern), it emits **separate** DetectorOutputs, one per threat type.

### Status

**PROPOSED.** Threat types are inherited from BD-008 (Active, not Locked).

---

## 16. Error / Non-Detection Outputs

### Decision enum

DetectorOutput uses an explicit `decision` field to distinguish structurally different outcomes:

| Decision | Meaning | `threat_type` present? | `confidence` present? | `evidence` present? |
|---|---|---|---|---|
| `no_threat` | Evaluation completed normally; no threat detected | No | Yes (confidence of no-threat assessment) | Optional |
| `detection` | Threat detected | Yes | Yes | Yes |
| `insufficient_data` | Not enough features available to make an assessment | No | No | Optional (may list what was missing) |
| `invalid_input` | Input failed validation (schema mismatch, unknown domain) | No | No | Optional (may describe the validation failure) |
| `detector_error` | Internal detector failure (model crash, timeout, exception) | No | No | Optional (may include error details for logging) |

### Design rationale

- **`no_threat` ≠ `detector_error`** — These must not be conflated. A successful evaluation that finds nothing suspicious is fundamentally different from a detector that crashed.
- **`insufficient_data` ≠ `no_threat`** — Not having enough data is not the same as having enough data and finding nothing. This distinction is important for operational monitoring (a detector consistently returning `insufficient_data` indicates a pipeline problem).
- **This is an internal contract** — API error handling for the analyst-facing REST/WebSocket layer is a separate concern and is not designed here.

### Status

**PROPOSED.**

---

## 17. Out-of-Scope / OPEN Handling

### Explicitly preserved as OPEN (not resolved by this document)

| Item | Upstream Source | Why OPEN |
|---|---|---|
| `repeated-destination behaviour` | Feature/Window v7 §4 | Feature semantics unresolved |
| Exfiltration `windowed transfer volume` | Feature/Window v7 §4 | Feature semantics unresolved |
| Exfiltration `large-transfer indicators` | Feature/Window v7 §4 | Feature semantics unresolved |
| Window durations / bucket widths / session gaps | Feature/Window v7 §8 | Benchmark-driven |
| Redis TTL values | Feature/Window v7 §9a.12 | Benchmark-driven |
| HLL vs exact-set for distinct-count | Feature/Window v7 §9a | PROPOSED / OPEN |
| Entropy frequency/distribution implementation | Feature/Window v7 §9a.2 | Implementation choice OPEN |
| Pair-state promotion thresholds / eviction / budgets | Feature/Window v7 §9a.5 | OPEN |
| Correlation timeout | Feature/Window v7 §9a.7 | OPEN |

### Explicitly preserved as OUT OF SCOPE FOR MVP

| Item | Reason |
|---|---|
| UDP amplification/asymmetry metrics | Sensor-placement / capture-point question unresolved (Architecture §12.1) |

### Rule

These items must **not** accidentally become required DetectorInput fields. If a detector input references an OPEN upstream feature, it must be marked as explicitly OPEN and must not be required.

### Status

**PROPOSED.**

---

## 18. Contract Compatibility

### Cross-check against existing schemas

| Existing Artefact | Compatibility Status |
|---|---|
| **Feature/Window v7 §5** (FeatureRecord envelope) | **Compatible.** DetectorInput passes through FeatureRecord fields without modification. |
| **Feature/Window v7 §4** (Detector-to-entity-and-mechanism mapping) | **Compatible.** §2 and §5–§10 of this document follow the same mapping. |
| **DATA_CONTRACTS.md** (threat taxonomy) | **Compatible.** Same 5 detector IDs and 6 threat types. |
| **`backend/app/schemas/alerts.py`** (AlertResponse) | **Compatible with noted differences.** AlertResponse is a *presentation* model for the dummy API. DetectorOutput is the *internal* detector contract. Differences: (1) AlertResponse has `evidence_summary` (string); DetectorOutput has structured `evidence` (object). (2) AlertResponse has `status` (analyst workflow); DetectorOutput has `decision` (detector outcome). (3) AlertResponse does not carry `source_feature_references` or `detector_version`. These differences are expected — AlertResponse will be updated during Alert Schema design. |
| **`backend/app/mock/data.py`** (MOCK_ALERTS) | **Compatible.** Mock alerts use the same detector IDs and threat types. The mock data is presentation-layer and does not need to implement DetectorOutput. |
| **API_CONTRACT.md** (dummy endpoints) | **Compatible.** The dummy API contract is explicitly temporary. DetectorOutput is an internal contract that does not affect the current dummy API. |
| **INTEGRATION_NOTES.md** | **No impact.** Current integration items are resolved frontend↔backend dummy items. |

### Documented differences (not conflicts)

The difference between DetectorOutput and AlertResponse is **by design** — they represent different layers in the architecture:

```text
DetectorOutput (detector's internal decision)
        ↓
Alert Engine (converts to alert)
        ↓
AlertResponse (analyst-facing presentation)
```

The Alert Schema design will bridge this gap explicitly.

### Status

**PROPOSED.**

---

## 19. Decision Status Summary

| Design Item | Status |
|---|---|
| Detector taxonomy (5 detectors, 6 threats) | **Inherited / not to be altered** (BD-008 Active) |
| detector_id ≠ threat_type | **Inherited** |
| Heterogeneous feature mechanisms permitted | **Inherited** (Architecture §11, Feature/Window §4) |
| FeatureRecord snapshot-not-delta invariant | **LOCKED** (Feature/Window §6) |
| DetectorInput envelope | **PROPOSED** |
| Typed payload strategy (Option C) | **PROPOSED** |
| Base grouping identity = `(detector_id, entity_key)` | **PROPOSED** |
| Temporal association policy for multi-mechanism detectors | **OPEN** — candidate approaches documented |
| `tls_c2_detector` multi-entity association | **OPEN** |
| Per-detector input contracts (§6–§10) | **PROPOSED** |
| Partial-input policy | **PROPOSED** |
| Revision passthrough from FeatureRecord | **PROPOSED** |
| Staleness detection (per-feature logical identity) | **OPEN** |
| Idempotency mechanism | **OPEN** |
| Authoritative DetectorOutput ordering | **OPEN** |
| DetectorOutput envelope | **PROPOSED** |
| Decision enum (no_threat / detection / insufficient_data / invalid_input / detector_error) | **PROPOSED** |
| Threat-type mapping | **PROPOSED** (inherited taxonomy) |
| Evidence structure | **PROPOSED** — baseline defined, refinement during Alert Schema |
| Confidence/score numerical semantics | **OPEN** |
| Exact detector version format | **OPEN** |
| Exact model version format | **OPEN** |
| Evaluation trigger model (push vs pull) | **OPEN** |
| Batching/invocation transport | **OPEN** |
| Final Alert mapping details | **OPEN** — downstream design step |

### Status discipline

Items marked **LOCKED** have explicit project-lead approval. **Inherited** items come from upstream documents with their stated status. **PROPOSED** items are structural baselines subject to review. **OPEN** items require implementation-driven resolution or depend on upstream decisions not yet made.

---

## 20. Review Checklist

Before promoting this document from DRAFT to FINAL, verify:

- [x] All five detector IDs verified against BD-008 and existing `alerts.py` enums
- [x] Detector → threat-type mapping consistent with BD-008 and DATA_CONTRACTS.md
- [x] FeatureRecord → DetectorInput relationship defined (§3)
- [x] Heterogeneous feature mechanisms handled (§2, §8, §9, §11)
- [x] Multi-window-type detectors have explicit association requirement and candidate approaches documented (§11); final policy remains OPEN
- [x] Partial-input behaviour defined (§12)
- [x] Revision/idempotency boundary defined (§13)
- [x] DetectorOutput separated from Alert Schema (§14, §18)
- [x] OPEN/out-of-scope upstream items preserved (§17)
- [x] No implementation code added
- [x] BD-008 status correctly represented as Active/inherited, not LOCKED
- [x] Enrichment records not forced into window fields (§3, §11)
- [ ] No window duration, TTL, or threshold value hard-coded
- [ ] Evidence structure reviewed during Alert Schema design
- [ ] Temporal association policy finalized during implementation
- [ ] `tls_c2_detector` multi-entity association finalized during implementation

---

## 21. Next Design Step

```text
Feature / Window Schema (v7)
        ↓
Detector Input / Output Contract (v1)  ← THIS DOCUMENT
        ↓
Alert Schema
        ↓
PostgreSQL Schema
        ↓
Final API Contract
```

### Design-chain discipline

- Detector I/O does **not** redefine Feature/Window.
- Alert Schema does **not** get finalized here.
- PostgreSQL Schema does **not** get finalized here.
- DetectorOutput is the detector's decision contract. The Alert Engine converts it into an alert — that conversion is the Alert Schema design step.
- Detector-specific payload details depend on feature mappings that remain PROPOSED or OPEN in Feature/Window v7 §4 (particularly `repeated-destination behaviour` and exfiltration transfer-volume semantics).
- The provenance question (Feature/Window §18) must be explicitly resolved before Alert Schema design begins to ensure alert explainability.

---

## 22. Final Status

**DRAFT v1 — Detector I/O structural contract complete.**

This revision establishes the DetectorInput and DetectorOutput envelopes, typed payload strategy, per-detector input contracts, feature grouping identity, partial-input policy, versioning/revision boundary, threat-type mapping, error/non-detection output taxonomy, and contract compatibility analysis.

Foundational items are inherited from upstream documents. No items are newly LOCKED. All structural definitions are **PROPOSED**. Temporal association policy, evaluation trigger model, exact version formats, confidence/score semantics, evidence structure details, and implementation-level idempotency are **OPEN**.

No detector runtime code, Redis keys, ML models, or Alert Schema fields should be implemented from this document until the proposed design is explicitly reviewed and approved.
