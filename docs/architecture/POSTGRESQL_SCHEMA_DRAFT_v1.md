# SIH26145 — POSTGRESQL SCHEMA (DRAFT v1)

> **Status:** DRAFT — structural PostgreSQL persistence model for review; individual section statuses vary (see §20). Requires project-lead / team review before promotion to `_FINAL`.
>
> **Continues from:** `docs/architecture/ALERT_SCHEMA_DRAFT_v1.md`, `docs/architecture/DETECTOR_IO_CONTRACT_DRAFT_v1.md`, and upstream design-chain documents.
>
> **Scope:** This document defines the **structural PostgreSQL data model** required to persist canonical alerts. It does **not** provide CREATE TABLE SQL, ORM models, migrations, deployment-specific PostgreSQL configuration, or exact physical index definitions — those are implementation concerns.

---

## 1. Design Inputs and Guardrails

This document sits in the design chain:

```text
Canonical Event Schema
        ↓
Redpanda Topics (v5)
        ↓
Feature / Window Schema (v7)
        ↓
Detector Input / Output Contract (v1)
        ↓
Alert Schema (v1)
        ↓
PostgreSQL Schema  ← THIS DOCUMENT
        ↓
Final API Contract
```

### Inherited constraints

**LOCKED / INHERITED (explicit project-lead approval):**

- PostgreSQL is durable alert truth (BD-003)
- Redis hot state and Pub/Sub are separate roles (BD-004)
- PostgreSQL INSERT commit precedes Redis Pub/Sub for alert publication (BD-005)
- DetectorOutput is the upstream decision/result contract
- Alert Schema is the canonical application-level alert contract
- PostgreSQL is downstream of Alert Schema
- Snapshot-not-delta processing invariant (Feature/Window §6)
- 5 detectors are logical modules, not microservices (Architecture §11)

**PROPOSED (upstream — not LOCKED):**

- UPDATE commit-before-notify extension (Alert Schema §4)
- Alert envelope (Alert Schema §3)
- Dedup identity structure (Alert Schema §9)
- Lifecycle status enum (Alert Schema §10)
- Evidence / provenance model (Alert Schema §7, §8)
- Versioning structure (Alert Schema §20)
- update_count baseline (Alert Schema §20)
- DetectorOutput envelope (Detector I/O v1 §14)
- Decision enum (Detector I/O v1 §16)
- Typed payload strategy — Option C (Detector I/O v1 §4)

**Inherited Active / not LOCKED (BD-008):**

- 5 detector IDs: `ddos_detector`, `recon_detector`, `dns_dga_tunnel_detector`, `tls_c2_detector`, `exfiltration_detector`
- 6 threat types: `volumetric_ddos`, `c2_beaconing`, `dga_dns_tunnel`, `encrypted_malware`, `recon_portscan`, `data_exfiltration`
- 5 severities: `critical`, `high`, `medium`, `low`, `info`
- detector_id ≠ threat_type

### What this document does NOT finalize

- CREATE TABLE SQL or DDL
- ORM model definitions
- Migration scripts
- Deployment-specific PostgreSQL configuration (connection pools, WAL, etc.)
- Exact physical index definitions
- Exact deduplication algorithm
- Temporal dedup scoping
- Exact stale-update/optimistic-locking algorithm
- Exact retention periods
- Exact partitioning strategy
- Final API contract
- Redis Pub/Sub implementation
- Cross-detector correlation/incident tables

### PHASE 0 verification checkpoint

A verification checkpoint was produced and approved before this document was written (see conversation record). All field extractions, status classifications, and entity-model findings in this document trace to that checkpoint.

### Status

**PROPOSED.** Design inputs are inherited; this section documents their provenance.

---

## 2. What Must Be Persisted

### Field classification

Every field from Alert Schema §3 is classified for PostgreSQL persistence:

| Alert Field | Persistence Classification | Rationale |
|---|---|---|
| `alert_id` | **REQUIRED** | Primary key; unique record identity |
| `detector_output_id` | **REQUIRED** | Current/latest DetectorOutput reference |
| `detector_id` | **REQUIRED** | Core classification; dedup component; index target |
| `threat_type` | **REQUIRED** | Core classification; dedup component; index target |
| `entity_type` | **REQUIRED** | Entity identity; dedup component; 5-value enum |
| `entity_key` | **REQUIRED** | Entity identity; dedup component; index target |
| `detected_at` | **REQUIRED** | Core timestamp; index target for time-range queries |
| `created_at` | **REQUIRED** | Record creation time |
| `first_seen_at` | **REQUIRED** | Dedup scope temporal bound |
| `last_seen_at` | **REQUIRED** | Dedup scope temporal bound; staleness reference |
| `status` | **REQUIRED** | Lifecycle state; index target |
| `severity` | **REQUIRED** | Alert Engine's final severity |
| `severity_candidate` | **REQUIRED** | Detector's severity suggestion; audit trail |
| `confidence` | **CONDITIONAL** | Present when DetectorOutput carries it; nullable |
| `score` | **OPTIONAL** | Raw detector score; nullable |
| `title` | **REQUIRED** | Analyst-facing alert title |
| `evidence_summary` | **REQUIRED** | Human-readable summary; separate from structured evidence |
| `evidence` | **REQUIRED** | Structured evidence (JSONB) |
| `source_feature_references` | **REQUIRED** | Provenance chain; list of `{feature_id, revision}` (JSONB) |
| `detector_version` | **REQUIRED** | Detector logic version |
| `model_version` | **CONDITIONAL** | ML model version; nullable for non-ML detectors |
| `schema_version` | **REQUIRED** | Alert Schema contract version |
| `dedup_identity` | **DERIVED** | Represented by component columns: `detector_id`, `threat_type`, `entity_type`, `entity_key` — no separate column |
| `update_count` | **REQUIRED** | Concurrency signal; revision counter |
| `resolved_at` | **CONDITIONAL** | Set on terminal status transitions; nullable |

### JSONB vs normalized

| Field | Representation | Reason |
|---|---|---|
| `evidence` | **JSONB** | Flexible structure; evolves per detector; investigation queries via JSONB operators |
| `source_feature_references` | **JSONB** | Variable-length list; per-feature revision semantics; no normalization benefit for MVP |
| `dedup_identity` | **Component columns** | The 4 constituent fields are already individual columns; no separate JSONB blob needed |
| All other fields | **Scalar columns** | Fixed structure; indexed; queried directly |

### Status

**PROPOSED.**

---

## 3. Entity Model Clarification

### Alert-level entity types (5 values)

Alert Schema §14 defines exactly 5 `entity_type` values:

| entity_type | entity_key format | Example |
|---|---|---|
| `source` | IP address | `10.0.2.15` |
| `destination` | IP address | `10.0.5.20` |
| `pair` | `src_ip\|dst_ip` | `10.0.2.15\|203.0.113.47` |
| `connection` | connection identifier | `conn_id_xyz` |
| `event` | event identifier | `event_id_abc` |

This is the **5-value** set from Alert Schema §14, not the 4-value set from Feature/Window (which does not include `event`).

### Alert-time identity/context durability finding

**Problem:** The canonical Alert's `entity_type` + `entity_key` does not always capture the full investigative context an analyst needs:

| entity_type | What entity_key captures | What is NOT captured |
|---|---|---|
| `source` | src_ip | dst_ip, ports |
| `destination` | dst_ip | src_ip, ports |
| `pair` | src_ip\|dst_ip | ports |
| `connection` | connection_id | IPs/ports not directly in key |
| `event` | event_id | IPs/ports not directly in key |

**Concrete example:** A DDoS alert with `entity_type=destination`, `entity_key=10.0.5.20` contains no source information. The AlertResponse mock data includes `src_ip="198.51.100.0/24"` for this same alert. Once upstream Redpanda/Redis retention windows expire, the provenance chain (Alert → source_feature_references → FeatureRecord → raw event) may not be followable, making the source context unrecoverable.

**Resolution:** Alert-time investigative context that cannot be durably reconstructed via provenance should be captured at alert-creation time within the existing `alert_context` sub-object of the `evidence` JSONB field (Alert Schema §7). The Alert Engine populates `alert_context` with representative entity context when constructing the alert — for example:

- DDoS destination alert → `alert_context.representative_sources: ["198.51.100.0/24"]`
- Exfiltration source alert → `alert_context.representative_destinations: ["suspicious-external.example.com"]`
- Pair alert → `alert_context.representative_ports: {src: 49210, dst: 443}`

This approach:
1. Uses the already-defined evidence JSONB structure — no new normalized columns
2. Does not copy AlertResponse's `src_ip`/`dst_ip`/`port` fields as PostgreSQL columns
3. Captures context durably before upstream retention expires
4. Leaves exact `alert_context` field names and structure OPEN for implementation

**What this does NOT do:**
- Does not add `src_ip`, `dst_ip`, `src_port`, `dst_port` as normalized Alert table columns
- Does not modify Alert Schema — the `alert_context` sub-object already exists in §7
- Does not assume AlertResponse's presentation fields are canonical

### Status

**PROPOSED** (alert-time context durability requirement). **OPEN** (exact `alert_context` entity-context fields).

---

## 4. Primary Entity Model

### MVP entities

**One primary entity: Alert**

No separate history/revision table in MVP.

### History/Revision strategy: A1 + B1

**Question A — History representation: A1**

Only the current Alert row is persisted. No separate immutable history/revision table.

**Reasoning:**
- Alert Schema §11 defines update behavior as in-place mutation
- Alert Schema does not define or require immutable history records
- `update_count` tracks how many updates occurred
- `source_feature_references` accumulates all contributing FeatureRecords across updates
- No existing architecture requirement for point-in-time alert snapshots
- A history table can be added later without breaking the current model

**Question B — Concurrency field: B1**

`update_count` is the current structural concurrency signal. This does not finalize the stale-update/optimistic-locking algorithm. PostgreSQL implementation will determine how `update_count` participates in compare-and-update or equivalent concurrency control. The exact stale-update algorithm remains **OPEN**.

**Reasoning:**
- Alert Schema §20 defines `update_count` as "sufficient for detecting concurrent-modification conflicts at the application level"
- No established difference in increment semantics between `update_count` and a hypothetical `alert_revision` has been identified
- Adding a redundant second counter without distinct semantics violates the "smallest viable model" preference
- Whether `update_count` alone is truly sufficient for all concurrency scenarios is an implementation decision, not a schema decision — it can be revisited during PostgreSQL implementation

**No field named bare `revision`** is introduced for the Alert row. The name `revision` is conceptually reserved for FeatureRecord revisions (Detector I/O §13) with per-feature, non-cross-comparable semantics. If a separate alert concurrency field is ever needed, it would use a distinct name such as `alert_revision`.

### What would change this decision

- Regulatory/compliance audit requirement for alert history → add AlertHistory table (A2)
- Proven concurrency failures with `update_count` alone → add `alert_revision` with distinct semantics (B2)
- Neither trigger exists in the current architecture

### Status

**PROPOSED** (A1 + B1). **OPEN** (whether history/additional concurrency field is ever needed).

---

## 5. Alert Table Structure

### Logical column definitions

| Column | Conceptual Type | Nullable | Mutability | Purpose |
|---|---|---|---|---|
| `alert_id` | UUID | NOT NULL | Immutable | Primary key |
| `detector_output_id` | UUID/text | NOT NULL | Mutable | Current/latest DetectorOutput |
| `detector_id` | text (enum) | NOT NULL | Immutable | Detector classification; dedup component |
| `threat_type` | text (enum) | NOT NULL | Immutable | Threat classification; dedup component |
| `entity_type` | text (enum) | NOT NULL | Immutable | Entity classification; dedup component; 5-value |
| `entity_key` | text | NOT NULL | Immutable | Entity identifier; dedup component |
| `detected_at` | timestamptz | NOT NULL | Immutable | Detector evaluation time (= DetectorOutput.evaluated_at) |
| `created_at` | timestamptz | NOT NULL | Immutable | Alert record construction time |
| `first_seen_at` | timestamptz | NOT NULL | Immutable | Earliest accepted detection time within resolved dedup scope |
| `last_seen_at` | timestamptz | NOT NULL | Mutable | Most recent accepted detection time within resolved dedup scope |
| `status` | text (enum) | NOT NULL | Mutable | Lifecycle: `new`, `investigating`, `closed`, `false_positive` |
| `severity` | text (enum) | NOT NULL | Mutable | Alert Engine's final severity |
| `severity_candidate` | text (enum) | NOT NULL | Mutable | Detector's severity suggestion |
| `confidence` | float | NULLABLE | Mutable | [0.0, 1.0]; null when not provided |
| `score` | float | NULLABLE | Mutable | Raw detector score; null when not provided |
| `title` | text | NOT NULL | Mutable | Analyst-facing alert title |
| `evidence_summary` | text | NOT NULL | Mutable | Human-readable evidence summary |
| `evidence` | JSONB | NOT NULL | Mutable | Structured evidence (detector_evidence + alert_context) |
| `source_feature_references` | JSONB | NOT NULL | Mutable | List of `{feature_id, revision}` objects |
| `detector_version` | text | NOT NULL | Mutable | Detector logic version |
| `model_version` | text | NULLABLE | Mutable | ML model version; null for non-ML |
| `schema_version` | text | NOT NULL | Immutable | Alert Schema contract version |
| `update_count` | integer | NOT NULL | Mutable | Concurrency signal; 0 on creation |
| `resolved_at` | timestamptz | NULLABLE | Mutable | Set on terminal status transition |
| `dedup_digest` | text | NULLABLE | Immutable | Optional hash of dedup components; exact algorithm OPEN |

### Timestamp representation

Alert Schema uses int64 epoch microseconds. PostgreSQL's `timestamptz` provides microsecond precision natively and supports time-range queries, indexing, and partition pruning without application-level conversion at query time.

**Proposed:** Store timestamps as `timestamptz` in PostgreSQL. Application-level conversion between int64 epoch microseconds and `timestamptz` occurs at the persistence boundary. This is a physical representation decision, not a change to Alert Schema's logical type.

### `dedup_digest` note

`dedup_digest` is **optional/PROPOSED** — a convenience column for fast dedup equality lookup. It is not a required physical field. The dedup identity is authoritatively represented by the four component columns (`detector_id`, `threat_type`, `entity_type`, `entity_key`). Whether `dedup_digest` is physically created depends on the implementation's query-performance findings. Its exact hashing/serialization algorithm remains **OPEN**.

### Status

**PROPOSED.**

---

## 6. Deduplication Persistence

### What must be persisted

The dedup identity = `(detector_id, threat_type, entity_type, entity_key)` (Alert Schema §9).

These four fields are already individual columns in the Alert table (§5). No separate dedup-identity column or table is needed.

### Dedup lookup support

The Alert Engine must search for an existing active alert with matching dedup identity when a new DetectorOutput arrives (Alert Schema §9). This requires:

1. **Component columns** — `detector_id`, `threat_type`, `entity_type`, `entity_key` are queryable individually and in combination
2. **Status filter** — dedup lookup only considers alerts in active lifecycle states (not `closed` or `false_positive`)
3. **Optional dedup_digest** — a computed hash of the four components for single-column equality lookup. PROPOSED, not required. Exact algorithm OPEN.
4. **Composite index** — a logical index on the dedup components + status supports the primary dedup access pattern (see §11)

### Temporal dedup scoping

Alert Schema §9 says temporal scoping remains **OPEN**. The column structure supports future temporal policy:
- If time-bounded: add a temporal dimension to the dedup lookup query (e.g. `AND last_seen_at > now() - interval`)
- If unbounded-until-resolved: filter by `status NOT IN ('closed', 'false_positive')`

No temporal column is added to the dedup identity. The policy is applied at query time.

### Status

**PROPOSED** (structural dedup persistence). **OPEN** (temporal scoping, exact dedup algorithm, dedup_digest algorithm).

---

## 7. Immutability Classification

### Immutable after creation

| Field | Reason |
|---|---|
| `alert_id` | Unique record identity; primary key |
| `detector_id` | Alert lineage identity — a detection from a different detector is a different alert |
| `threat_type` | Alert lineage identity — different threat types produce different alerts (MVP §12) |
| `entity_type` | Alert lineage identity — same entity_type is part of dedup identity |
| `entity_key` | Alert lineage identity — same entity_key is part of dedup identity |
| `detected_at` | Original detection time (Alert Schema §11: "Unchanged — preserves original detection time") |
| `created_at` | Record construction time |
| `first_seen_at` | Earliest detection in dedup scope (Alert Schema §3: "unchanged on updates") |
| `schema_version` | Contract version at creation time |
| `dedup_digest` | Derived from immutable dedup components |

### Mutable (updated by Alert Engine or analyst)

| Field | Update source | Update behavior |
|---|---|---|
| `detector_output_id` | Alert Engine | Updated to latest triggering DetectorOutput (§11) |
| `last_seen_at` | Alert Engine | Updated to new DetectorOutput's evaluated_at (§11) |
| `status` | Analyst | Analyst-initiated lifecycle transitions (§10) |
| `severity` | Alert Engine | Re-evaluated on updates; may change (§11) |
| `severity_candidate` | Alert Engine | Updated to latest detector suggestion (§11) |
| `confidence` | Alert Engine | Updated if new value is higher; exact policy OPEN (§11) |
| `score` | Alert Engine | Updated with latest detector score |
| `title` | Alert Engine | May be regenerated on updates |
| `evidence_summary` | Alert Engine | Regenerated on updates |
| `evidence` | Alert Engine | Merged/updated; exact merge strategy OPEN (§11) |
| `source_feature_references` | Alert Engine | Extended with new DetectorOutput's references (§11) |
| `detector_version` | Alert Engine | Updated to latest detector version |
| `model_version` | Alert Engine | Updated to latest model version |
| `update_count` | Alert Engine | Incremented on each valid update (§11) |
| `resolved_at` | Analyst | Set when status transitions to `closed` or `false_positive` |

### Verification against Alert Schema §11

All mutable fields are consistent with Alert Schema §11's update behavior table. No contradictions found.

### Status

**PROPOSED.**

---

## 8. Lifecycle Persistence

### Status enum

```text
new | investigating | closed | false_positive
```

This is the existing lifecycle from Alert Schema §10, reused from `backend/app/schemas/alerts.py`.

### Persistence rules

| Aspect | PostgreSQL behavior |
|---|---|
| **Initial status** | `new` — set by Alert Engine at alert creation |
| **Transitions** | Analyst-initiated: `new → investigating → closed`, `new → false_positive`, `investigating → false_positive`, etc. |
| **Terminal statuses** | `closed` and `false_positive` are terminal (analyst workflow completion) |
| **resolved_at** | Set (non-null) only when status transitions to `closed` or `false_positive` |
| **Detector updates** | Do NOT change status — analyst workflow is structurally separate from detector decisions (Alert Schema §11) |

### Status history

Whether the database stores status-transition history (e.g. a separate status_log table) is an implementation decision. Alert Schema does not require it. For MVP, the current status and `resolved_at` timestamp are sufficient.

### Status

**PROPOSED.**

---

## 9. Evidence Storage

### Storage strategy: JSONB

| Field | Storage | Reason |
|---|---|---|
| `evidence` | JSONB column | Structured detector evidence + alert_context; flexible schema; evolves per detector; investigation queries via JSONB operators |
| `evidence_summary` | Separate text column | For display without JSONB parsing; frequently accessed in list views |

### Evidence structure (inherited from Alert Schema §7)

```text
evidence (JSONB):
  detector_evidence:
    features_used: [{feature_name, value, contribution}, ...]
    features_missing: [{feature_name, reason}, ...]
    summary: "string"
  alert_context:
    dedup_action: "created" | "updated"
    severity_override: bool
    [alert-time entity context — see §3]
```

### Alert-time entity context in evidence

Per the Entity Model Clarification (§3), representative source/destination context is captured in `alert_context` within the JSONB evidence at alert-creation time. This ensures alert-time investigative context survives upstream retention expiry without adding normalized columns.

### Why JSONB

1. **Flexible schema** — different detectors produce different evidence structures
2. **Evolution** — new detectors or evidence fields don't require schema migrations
3. **Investigation queries** — PostgreSQL JSONB operators support querying evidence content
4. **Single column** — avoids a normalized evidence-detail table that would add complexity without clear benefit
5. **Alert_context** — the proposed entity-context capture fits naturally in JSONB

### Why NOT normalized evidence tables

- Evidence structure varies per detector and threat type
- Normalization would require a schema migration for every evidence-structure change
- JSONB operators provide adequate query capability for investigation
- No identified access pattern requires relational joins into evidence sub-fields

### Status

**PROPOSED** (JSONB strategy). **OPEN** (exact evidence field typing, exact alert_context sub-fields).

---

## 10. Provenance Storage

### Stored provenance references

| Field | Storage | Description |
|---|---|---|
| `detector_output_id` | UUID/text column | Reference to current/latest DetectorOutput |
| `source_feature_references` | JSONB column | List of `{feature_id, revision}` objects |
| `detector_version` | text column | Detector logic version |
| `model_version` | text column (nullable) | ML model version |

### Design principles

1. **References, not copies.** PostgreSQL stores references to upstream objects, not copies of raw events, FeatureRecords, or DetectorOutputs. The provenance chain is: Alert → DetectorOutput → FeatureRecords → raw events.

2. **Logical references only.** `detector_output_id` and items in `source_feature_references` are logical references. The upstream architecture does not require a durable DetectorOutput PostgreSQL table. DetectorOutputs live in Redpanda and are consumed by the Alert Engine; they are not separately persisted in PostgreSQL unless a future requirement demands it.

3. **Exception: alert-time entity context.** The one narrow exception to "references, not copies" is alert-time investigative context (§3). When upstream provenance may not be reconstructable after retention expiry, the Alert Engine captures representative context in `alert_context` JSONB at creation time. This is a specific, documented exception, not a general pattern of copying upstream data.

4. **`source_feature_references` as JSONB.** The list is variable-length, each entry carries its own per-feature `revision` (not cross-comparable per Detector I/O §13), and the list grows on alert updates (§11). JSONB is appropriate; a normalized join table would add complexity without benefit.

### What is NOT stored

- Raw events
- CanonicalEvents
- FeatureRecords
- DetectorInput records
- Full DetectorOutput records

These remain in their respective storage (Redpanda, Redis hot state) subject to their own retention policies.

### Status

**PROPOSED.**

---

## 11. Indexing Requirements

### Logical access patterns

| Access Pattern | Fields | Use Case |
|---|---|---|
| **Alert lookup** | `alert_id` | Single-alert retrieval (API, investigation) |
| **Dedup lookup** | `detector_id`, `threat_type`, `entity_type`, `entity_key`, `status` | Alert Engine dedup evaluation; find existing active alert for same logical identity |
| **Detector/threat filter** | `detector_id`, `threat_type` | Dashboard filtering; detector-specific alert views |
| **Entity lookup** | `entity_type`, `entity_key` | "Show all alerts for this IP" investigation |
| **Status filter** | `status` | Active alerts view; resolved alerts archive |
| **Time range** | `detected_at` | Time-based dashboard views; "alerts in last 24 hours" |
| **Recent alerts** | `created_at` or `detected_at` | "Most recent N alerts" for dashboard/API |
| **Active recent** | `status`, `detected_at` | Active alerts within a time range |
| **Severity filter** | `severity` | Critical/high alert views |

### Structural requirements vs physical implementation

The access patterns above are **structural requirements**. The exact index definitions (B-tree, composite, partial, GIN for JSONB, etc.) are **physical implementation decisions** left to the PostgreSQL implementation pass.

### Candidate composite indexes (logical)

| Candidate | Fields | Rationale |
|---|---|---|
| Primary key | `alert_id` | Unique identity |
| Dedup composite | `(detector_id, threat_type, entity_type, entity_key, status)` | Primary dedup lookup; the most performance-critical query |
| Entity composite | `(entity_type, entity_key)` | Cross-detector entity investigation |
| Time range | `(detected_at)` | Time-based queries; possible partition key |
| Status + time | `(status, detected_at)` | Active alerts in time range |

### Optional dedup_digest index

If `dedup_digest` is implemented, a single-column index on `dedup_digest` could replace the 4-column dedup composite for equality lookups. This is **PROPOSED**, not required.

### Status

**PROPOSED** (access patterns). **OPEN** (exact index definitions, physical types).

---

## 12. Constraints / Integrity

### Logical integrity rules

| Rule | Fields | Description |
|---|---|---|
| **Unique identity** | `alert_id` | Must be unique across all alert records |
| **Detector taxonomy** | `detector_id` | Must be one of the 5 inherited detector IDs (BD-008 Active) |
| **Threat taxonomy** | `threat_type` | Must be one of the 6 inherited threat types (BD-008 Active) |
| **Entity type** | `entity_type` | Must be one of the 5 values: `source`, `destination`, `pair`, `connection`, `event` (Alert Schema §14) |
| **Entity key coherence** | `entity_type`, `entity_key` | entity_key format must be consistent with entity_type (IP for source/destination, `src_ip\|dst_ip` for pair, identifier for connection/event) |
| **Temporal ordering** | `first_seen_at`, `last_seen_at` | `first_seen_at ≤ last_seen_at` |
| **Temporal ordering** | `created_at`, `detected_at` | No strict ordering required — detected_at may precede created_at (detection time vs persistence time) |
| **Update count** | `update_count` | `≥ 0` |
| **Confidence range** | `confidence` | `[0.0, 1.0]` when not null (inherited from DetectorOutput contract) |
| **Terminal resolution** | `resolved_at`, `status` | `resolved_at` must be non-null when `status ∈ {closed, false_positive}`; must be null when `status ∈ {new, investigating}` |
| **Status values** | `status` | Must be one of: `new`, `investigating`, `closed`, `false_positive` |
| **Severity values** | `severity`, `severity_candidate` | Must be one of: `critical`, `high`, `medium`, `low`, `info` |

### Detector/threat relationship

`detector_id` and `threat_type` are **distinct semantic fields** — they are NOT the same concept. A single detector may emit multiple threat types (e.g. `tls_c2_detector` → `c2_beaconing` or `encrypted_malware`). This is a taxonomy relationship (Detector I/O §2, Alert Schema §2), not a row-level inequality constraint. The valid combinations are defined by the detector→threat mapping, but enforcing the mapping as a database constraint is an implementation decision.

### Implementation note

These are **logical integrity rules**, not PostgreSQL CHECK constraint syntax. Whether each rule is enforced as a CHECK constraint, ENUM type, application-level validation, or trigger is an implementation decision.

### Status

**PROPOSED.**

---

## 13. Foreign Keys / References

### Classification

| Reference | Type | Reason |
|---|---|---|
| `alert_id` (PK) | Actual primary key | Standard relational identity |
| `detector_output_id` | **Logical reference only** | DetectorOutput does not have a PostgreSQL table; it lives in Redpanda and is consumed by the Alert Engine. No FK target exists. |
| `source_feature_references` | **Logical references only** | FeatureRecords do not have a PostgreSQL table; they live in Redpanda/Redis. JSONB list of `{feature_id, revision}` objects. No FK target exists. |
| `detector_id` | **Logical reference** | Could reference a detector lookup table if one is created, but the detector taxonomy is currently an application-level constant (BD-008 Active), not a PostgreSQL relation. |
| `threat_type` | **Logical reference** | Same as detector_id — taxonomy is application-level. |

### No invented tables

This document does not create a DetectorOutput table, FeatureRecord table, detector lookup table, or threat-type lookup table merely to support foreign keys. The upstream architecture does not require these as durable PostgreSQL entities.

If a future implementation introduces:
- A detector/threat lookup table → `detector_id`/`threat_type` could become actual FKs
- A DetectorOutput persistence table → `detector_output_id` could become an actual FK

These are future decisions, not current requirements.

### Status

**PROPOSED.**

---

## 14. Retention

### PostgreSQL retention role

PostgreSQL is the **durable alert truth** (BD-003). Alerts persisted to PostgreSQL are expected to outlive all upstream ephemeral storage (Redpanda topics, Redis hot state).

### Retention differentiation

| Data | Retention | Notes |
|---|---|---|
| **Alert records** | Long-term / indefinite | Alerts are the primary investigative record. Exact retention period depends on compliance, operational, and storage requirements. |
| **Evidence JSONB** | Same as alert record | Evidence is part of the alert row; retained as long as the alert exists |
| **source_feature_references JSONB** | Same as alert record | Provenance references are part of the alert row |
| **Dedup digest** | Same as alert record | Derived from immutable components; retained with the alert |

### What remains OPEN

- Exact alert retention period (days, months, indefinite)
- Whether old closed/false_positive alerts are archived or purged
- Whether a separate archive strategy is needed
- Whether evidence JSONB should be truncated/summarized after a retention period while keeping the alert metadata

### Distinction from upstream retention

| System | Retention scope | Governed by |
|---|---|---|
| Redpanda | Raw events, FeatureRecords, DetectorOutputs | Redpanda topic retention config |
| Redis | Hot state, rolling counters | Redis TTL / eviction policy |
| PostgreSQL | Alerts (this document) | Alert retention policy (OPEN) |

These are independent. PostgreSQL alert retention does not depend on Redpanda/Redis retention. Alerts survive upstream retention expiry — this is why alert-time entity context capture (§3) is important.

### Status

**PROPOSED** (retention differentiation). **OPEN** (exact retention periods, archive strategy).

---

## 15. Partitioning

### Evaluation

| Factor | Assessment |
|---|---|
| **MVP alert volume** | Unknown; no production traffic data exists yet. The system is still in dummy/scaffold phase. |
| **Time-based queries** | Primary time dimension is `detected_at`. Time-range queries are common in SOC dashboards. |
| **Retention** | If time-based retention is eventually implemented, range partitioning on `detected_at` would simplify retention management (DROP PARTITION vs DELETE). |
| **Implementation complexity** | Partitioning adds complexity to schema management, queries, and migrations. Not justified without volume evidence. |
| **Current evidence** | Insufficient to justify partitioning in MVP. |

### What would drive the decision

Partitioning becomes justified when:
- Alert volume reaches a scale where single-table performance degrades
- Time-based retention is implemented and DROP PARTITION is preferable to DELETE
- Query patterns consistently use time-range predicates as the primary filter

### Recommendation

**OPEN** for MVP. Do not implement partitioning without production volume data. The `detected_at` column is designed to support future range partitioning if needed.

### Status

**OPEN.**

---

## 16. Concurrency / Stale Update Support

### Structural support

`update_count` is the current structural concurrency signal (Alert Schema §20, A1 + B1 from §4 of this document).

### How it participates

`update_count` provides:
- **Ordering signal** — monotonically increasing per alert row
- **Optimistic locking candidate** — can be used in compare-and-update patterns (e.g. `UPDATE ... WHERE alert_id = $1 AND update_count = $expected`)
- **Staleness indicator** — the Alert Engine can compare incoming DetectorOutput's `evaluated_at` against the alert's `last_seen_at` before deciding to update

### What this does NOT finalize

This section defines the structural fields available for concurrency control. It does **not** finalize:

- The exact stale-update/optimistic-locking algorithm
- Whether `update_count` alone is sufficient for all concurrency scenarios
- Whether `last_seen_at` comparison is used alongside or instead of `update_count`
- Whether additional application-level locking (e.g. advisory locks, SELECT FOR UPDATE) is needed
- The exact retry/conflict-resolution behavior

These are implementation decisions for the PostgreSQL implementation pass.

### No bare `revision` field

No field named bare `revision` is introduced. The name `revision` is conceptually reserved for FeatureRecord revisions (Detector I/O §13) with per-feature, non-cross-comparable semantics. `update_count` serves the alert-row concurrency role. If a separate alert concurrency field is ever needed, it would use a distinct name such as `alert_revision`.

### Status

**PROPOSED** (structural support via `update_count`). **OPEN** (exact algorithm, whether additional fields/mechanisms are needed).

---

## 17. Transaction Boundary

### Preserved ordering

```text
Alert Engine
        ↓
PostgreSQL INSERT (new alert) or UPDATE (existing alert)
        ↓
AWAIT COMMIT
        ↓
success?
   ├── NO  → log/retry, do NOT publish
   └── YES → Redis Pub/Sub
```

### Status discipline

- **INSERT commit-before-publish:** **LOCKED** (BD-005)
- **UPDATE commit-before-publish:** **PROPOSED** (Alert Schema §4 extension)

BD-005's original wording references INSERT. Alert Schema §4 proposes extending the same invariant to UPDATE operations. This extension is PROPOSED, not LOCKED.

### No-op duplicates

No-op duplicate DetectorOutputs (same dedup identity, no new information) do not reach PostgreSQL or Redis Pub/Sub (Alert Schema §4).

### What this document does NOT design

- Redis Pub/Sub channel/topic names
- Redis Pub/Sub message format
- Retry/failure behavior details
- Connection pool management

### Status

**PROPOSED** (preserves existing ordering). INSERT ordering is **LOCKED** (BD-005). UPDATE ordering is **PROPOSED**.

---

## 18. API Boundary

### Separation of concerns

```text
Canonical Alert (Alert Schema)
        ↓
PostgreSQL persistence model (this document)
        ↓
API presentation model (Final API Contract)
```

### What this means

- PostgreSQL columns are designed to persist the canonical Alert, not to mirror AlertResponse
- AlertResponse may expose a subset of persisted fields, rename fields, or add computed fields
- The Final API Contract pass will define the exact AlertResponse ↔ PostgreSQL mapping
- PostgreSQL does not add columns merely because AlertResponse currently has a field

### AlertResponse gap analysis

AlertResponse currently has `src_ip`, `src_port`, `dst_ip`, `dst_port` fields that are not canonical Alert fields and are not PostgreSQL columns. Per the Entity Model Clarification (§3), alert-time entity context is captured in `alert_context` JSONB. The Final API Contract pass will determine how to populate AlertResponse's IP/port fields from the canonical Alert:

- `entity_type=pair` → parse `entity_key` for src_ip/dst_ip
- `entity_type=source` → entity_key = src_ip; dst_ip from `alert_context` (if captured)
- `entity_type=destination` → entity_key = dst_ip; src_ip from `alert_context` (if captured)
- Port information → from `alert_context` (if captured)

This mapping is a Final API Contract concern, not a PostgreSQL schema concern.

### Status

**PROPOSED.**

---

## 19. Logical Field Mapping

### Alert field → PostgreSQL representation

| Alert Field | PG Type | Column | Nullable | Mutable | Notes |
|---|---|---|---|---|---|
| `alert_id` | UUID | `alert_id` | NOT NULL | Immutable | Primary key |
| `detector_output_id` | UUID/text | `detector_output_id` | NOT NULL | Mutable | Current/latest |
| `detector_id` | text (enum) | `detector_id` | NOT NULL | Immutable | Dedup component |
| `threat_type` | text (enum) | `threat_type` | NOT NULL | Immutable | Dedup component |
| `entity_type` | text (enum) | `entity_type` | NOT NULL | Immutable | 5-value; dedup component |
| `entity_key` | text | `entity_key` | NOT NULL | Immutable | Dedup component |
| `detected_at` | timestamptz | `detected_at` | NOT NULL | Immutable | int64 → timestamptz conversion |
| `created_at` | timestamptz | `created_at` | NOT NULL | Immutable | int64 → timestamptz conversion |
| `first_seen_at` | timestamptz | `first_seen_at` | NOT NULL | Immutable | Dedup scope bound |
| `last_seen_at` | timestamptz | `last_seen_at` | NOT NULL | Mutable | Dedup scope bound |
| `status` | text (enum) | `status` | NOT NULL | Mutable | 4-value lifecycle |
| `severity` | text (enum) | `severity` | NOT NULL | Mutable | 5-value |
| `severity_candidate` | text (enum) | `severity_candidate` | NOT NULL | Mutable | 5-value |
| `confidence` | float | `confidence` | NULLABLE | Mutable | [0.0, 1.0] |
| `score` | float | `score` | NULLABLE | Mutable | Raw detector score |
| `title` | text | `title` | NOT NULL | Mutable | |
| `evidence_summary` | text | `evidence_summary` | NOT NULL | Mutable | Separate from JSONB evidence |
| `evidence` | JSONB | `evidence` | NOT NULL | Mutable | detector_evidence + alert_context |
| `source_feature_references` | JSONB | `source_feature_references` | NOT NULL | Mutable | [{feature_id, revision}, ...] |
| `detector_version` | text | `detector_version` | NOT NULL | Mutable | |
| `model_version` | text | `model_version` | NULLABLE | Mutable | Null for non-ML |
| `schema_version` | text | `schema_version` | NOT NULL | Immutable | |
| `update_count` | integer | `update_count` | NOT NULL | Mutable | ≥ 0; default 0 |
| `resolved_at` | timestamptz | `resolved_at` | NULLABLE | Mutable | Set on terminal status |
| `dedup_identity` | — | (derived) | — | — | Represented by 4 component columns |
| `dedup_digest` | text | `dedup_digest` | NULLABLE | Immutable | Optional/PROPOSED; hash of dedup components |

### Status

**PROPOSED.**

---

## 20. Decision Status Summary

| Design Item | Status |
|---|---|
| PostgreSQL is durable alert truth | **LOCKED** (BD-003) |
| Redis hot state and Pub/Sub are separate roles | **LOCKED** (BD-004) |
| PostgreSQL INSERT commit precedes Redis Pub/Sub | **LOCKED** (BD-005) |
| UPDATE commit-before-publish extension | **PROPOSED** (Alert Schema §4) |
| Alert Schema is canonical application-level contract | **Inherited PROPOSED baseline** |
| PostgreSQL is downstream of Alert Schema | **Inherited PROPOSED baseline** |
| Alert envelope | **Inherited PROPOSED baseline** (Alert Schema §3) |
| Dedup identity structure | **Inherited PROPOSED baseline** (Alert Schema §9) |
| Lifecycle status enum | **Inherited PROPOSED baseline** (Alert Schema §10) |
| Evidence structure | **Inherited PROPOSED baseline** (Alert Schema §7) |
| Versioning structure | **Inherited PROPOSED baseline** (Alert Schema §20) |
| update_count baseline | **Inherited PROPOSED baseline** (Alert Schema §20) |
| Detector taxonomy (5 IDs, 6 threats) | **Inherited Active / not LOCKED** (BD-008) |
| detector_id ≠ threat_type | **Inherited** (BD-008 Active) |
| Alert table logical structure | **PROPOSED** |
| A1 — no separate history table in MVP | **PROPOSED** |
| B1 — update_count as structural concurrency signal | **PROPOSED** |
| JSONB evidence storage | **PROPOSED** |
| JSONB source_feature_references storage | **PROPOSED** |
| Dedup persistence via component columns | **PROPOSED** |
| dedup_digest (optional) | **PROPOSED** |
| Alert-time entity context durability requirement | **PROPOSED** |
| Immutability classification | **PROPOSED** |
| Lifecycle persistence model | **PROPOSED** |
| Provenance via references | **PROPOSED** |
| Indexing access patterns | **PROPOSED** |
| Integrity rules | **PROPOSED** |
| Logical-reference-only FK strategy | **PROPOSED** |
| Timestamp representation (timestamptz) | **PROPOSED** |
| Transaction ordering (INSERT LOCKED, UPDATE PROPOSED) | Per source status |
| API boundary | **PROPOSED** |
| Exact physical SQL types/constraints | **OPEN** |
| Exact index definitions | **OPEN** |
| Exact partitioning | **OPEN** |
| Exact retention periods | **OPEN** |
| Exact dedup algorithm | **OPEN** |
| Temporal dedup scope | **OPEN** |
| Exact stale-update/optimistic-locking algorithm | **OPEN** |
| History granularity (if ever needed) | **OPEN** |
| Exact alert_context entity-context fields | **OPEN** |
| Advanced incident storage | **OPEN** |
| Deployment-specific PostgreSQL configuration | **OPEN** |
| Whether `alert_revision` field is ever needed | **OPEN** |
| dedup_digest hashing/serialization algorithm | **OPEN** |
| Evidence JSONB retention/truncation policy | **OPEN** |

### Status discipline

Items marked **LOCKED** have explicit project-lead approval. **Inherited PROPOSED baseline** items come from upstream documents at PROPOSED status. **Inherited Active / not LOCKED** items come from BD-008 (Active, not Locked). **PROPOSED** items are structural baselines defined by this document, subject to review. **OPEN** items require implementation-driven resolution.

---

## 21. Review Checklist

- [x] PHASE 0 verification checkpoint produced and approved before this document was written
- [x] Alert Schema v1 used as primary source
- [x] PostgreSQL durable-truth role preserved (BD-003)
- [x] All persistent Alert fields classified (§2)
- [x] entity_type verified as the 5-value enum from Alert Schema §14, not a 4-value assumption from Feature/Window
- [x] Alert-time identity/context durability question explicitly investigated and documented (§3), not silently resolved
- [x] No PostgreSQL field named bare `revision` for an Alert-row concept (§4, §16)
- [x] Primary Alert entity defined (§4, §5)
- [x] Deduplication persistence defined (§6)
- [x] History/revision strategy addressed — A1 + B1, both questions answered explicitly (§4)
- [x] Lifecycle persistence defined (§8)
- [x] Evidence storage boundary defined — JSONB (§9)
- [x] Provenance references preserved — logical references, not copies (§10)
- [x] Alert-time entity context exception documented (§3, §10)
- [x] Indexing access patterns documented (§11)
- [x] Integrity rules documented (§12)
- [x] Concurrency/stale-update support addressed — structural fields defined, algorithm OPEN (§16)
- [x] Transaction ordering preserved — INSERT LOCKED (BD-005), UPDATE PROPOSED (§17)
- [x] Retention/partitioning status documented (§14, §15)
- [x] API boundary preserved (§18)
- [x] BACKEND_CONTEXT.md drift checked and corrected (Task 22B)
- [ ] No SQL implemented
- [ ] No API finalized
- [ ] No runtime code added

The unchecked items are post-execution verification — they will be confirmed by `git status`.

---

## 22. Cross-Document Consistency

### Compatibility with existing artefacts

| Artefact | Compatibility Status |
|---|---|
| **ALERT_SCHEMA_DRAFT_v1.md §3** (Alert envelope) | **Compatible.** All 25 canonical fields accounted for. Field classifications match §3's Required/Conditional/Optional. |
| **ALERT_SCHEMA_DRAFT_v1.md §9** (Dedup identity) | **Compatible.** Structural dedup key persisted via component columns. Temporal scoping remains OPEN in both documents. |
| **ALERT_SCHEMA_DRAFT_v1.md §11** (Update behavior) | **Compatible.** Immutable/mutable classification matches §11's update table. `detector_output_id` correctly mutable. |
| **ALERT_SCHEMA_DRAFT_v1.md §14** (Entity types) | **Compatible.** 5-value entity_type enum used, including `event`. |
| **ALERT_SCHEMA_DRAFT_v1.md §17** (PostgreSQL boundary) | **Compatible.** This document implements §17's structural boundary. No SQL tables yet. |
| **ALERT_SCHEMA_DRAFT_v1.md §20** (Versioning) | **Compatible.** `update_count` as concurrency signal, exact algorithm OPEN. |
| **DETECTOR_IO_CONTRACT_DRAFT_v1.md §13** (Revision) | **Compatible.** No `revision` naming collision. `source_feature_references` carries per-feature `{feature_id, revision}` objects in JSONB. |
| **DETECTOR_IO_CONTRACT_DRAFT_v1.md §14** (DetectorOutput) | **Compatible.** `detector_output_id` maps to DetectorOutput.output_id. No DetectorOutput PostgreSQL table assumed. |
| **BACKEND_DECISIONS.md BD-003** | **Compatible.** PostgreSQL is durable truth. |
| **BACKEND_DECISIONS.md BD-005** | **Compatible.** INSERT ordering LOCKED. UPDATE extension PROPOSED. |
| **BACKEND_DECISIONS.md BD-008** | **Compatible.** Active status preserved, not promoted to Locked. |
| **`backend/app/schemas/alerts.py`** (AlertResponse) | **Compatible with noted differences.** AlertResponse's `src_ip`/`dst_ip`/`port` fields are presentation fields, not canonical Alert columns. Entity context durability addressed via `alert_context` JSONB. Gap documented in §3 and §18. |
| **DATA_CONTRACTS.md** | **Compatible.** Same design chain. Item 6 updated. |

### Naming collision verification

- No field named bare `revision` introduced for Alert-row concept
- `revision` appears only inside `source_feature_references` JSONB as per-feature FeatureRecord revision (Detector I/O §13)
- `update_count` is the alert-row concurrency signal
- No terminology collision identified

### Status

**PROPOSED.**

---

## 23. Next Design Step

```text
Feature / Window Schema (v7)
        ↓
Detector Input / Output Contract (v1)
        ↓
Alert Schema (v1)
        ↓
PostgreSQL Schema (v1)  ← THIS DOCUMENT
        ↓
Final API Contract
```

### Design-chain discipline

- PostgreSQL Schema does **not** redefine Alert Schema, Detector I/O, or Feature/Window
- Final API Contract does **not** get finalized here
- The Final API Contract pass should use Alert Schema, PostgreSQL Schema, and the existing AlertResponse as inputs
- The AlertResponse ↔ canonical Alert ↔ PostgreSQL mapping is a Final API Contract concern

---

## 24. Final Status

**DRAFT v1 — PostgreSQL persistence model structural contract complete.**

This revision establishes the logical Alert table, field classification (Required/Conditional/Optional/Derived), immutability classification, JSONB evidence storage, dedup persistence via component columns, entity-model clarification with alert-time context durability finding, history/revision strategy (A1 + B1), lifecycle persistence, provenance references, indexing access patterns, integrity rules, concurrency support structure, retention differentiation, transaction boundary, and API boundary.

Foundational items are inherited from upstream documents with their stated statuses (LOCKED, PROPOSED, Active). No items are newly LOCKED. All structural definitions are **PROPOSED**. Exact SQL types, index definitions, partitioning, retention periods, dedup algorithm, stale-update algorithm, alert_context entity-context fields, and deployment configuration are **OPEN**.

No PostgreSQL tables, SQL, ORM models, migrations, or runtime code should be created from this document until the proposed design is explicitly reviewed and approved.
