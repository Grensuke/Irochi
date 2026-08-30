# SIH26145 — FINAL API CONTRACT (DRAFT v1)

> **Status:** DRAFT — presentation contract for review; individual section statuses vary (see §23). Requires project-lead / team review before promotion to `_FINAL`.
>
> **Continues from:** `docs/architecture/ALERT_SCHEMA_DRAFT_v1.md`, `docs/architecture/POSTGRESQL_SCHEMA_DRAFT_v1.md`, and upstream design-chain documents.
>
> **Scope:** This document defines the **Final API Contract** — the presentation layer that exposes canonical Alert, dashboard, and health data to the frontend and external consumers. It does **not** provide FastAPI implementation code, Pydantic models, authentication mechanisms, or deployment configuration.
>
> **PHASE 0 verification checkpoint:** Produced and approved before this document was written (see conversation record).
>
> **PHASE 1 implementation plan:** Produced and approved before this document was written (see conversation record).

---

## 1. Design Chain Position

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
PostgreSQL Schema (v1)
        ↓
API Contract (Draft v1)     ← THIS DOCUMENT
```

### API contract role

This is a **presentation contract**. It must not become:
- a new source of truth
- a replacement for Alert Schema
- a replacement for PostgreSQL Schema
- a place to redefine detector semantics

All canonical definitions remain authoritative in their upstream documents. This document formalizes how those definitions are exposed at the API boundary.

### Status

**PROPOSED** (this document). Upstream documents carry their own statuses.

---

## 2. Inherited Constraints

**LOCKED / INHERITED (explicit project-lead approval):**

- PostgreSQL is durable alert truth (BD-003)
- Redis hot state and Pub/Sub are separate roles (BD-004)
- PostgreSQL INSERT commit precedes Redis Pub/Sub for alert publication (BD-005)

**Inherited PROPOSED (upstream, not LOCKED):**

- API is a presentation layer over the canonical application contracts
- Alert Schema is the canonical application-level Alert contract
- PostgreSQL is the persistence source beneath Alert Schema
- Existing endpoint purposes and REST surface from current API scaffold
- `/api/v1/` versioned prefix (established in runtime `config.py`)
- Alert presentation fields
- AlertResponse field mapping
- Dashboard response structure
- WebSocket presentation envelope
- API filtering/pagination structure
- Error response structure
- PostgreSQL UPDATE commit-before-publish (Alert Schema §4)

**Inherited Active / not LOCKED (BD-008):**

- 5 detector IDs: `ddos_detector`, `recon_detector`, `dns_dga_tunnel_detector`, `tls_c2_detector`, `exfiltration_detector`
- 6 threat types: `volumetric_ddos`, `c2_beaconing`, `dga_dns_tunnel`, `encrypted_malware`, `recon_portscan`, `data_exfiltration`
- 5 severities: `critical`, `high`, `medium`, `low`, `info`
- `detector_id` ≠ `threat_type`

### What this document does NOT finalize

- FastAPI route implementation
- Pydantic model definitions
- Authentication / authorization details
- Rate limiting
- Caching policy
- Deployment-specific gateway configuration
- Exact pagination defaults/limits
- Exact filter combinations
- Exact error body wording
- WebSocket heartbeat/reconnect policy
- Exact exposure of structured evidence/provenance
- Future API v2 migration strategy

---

## 3. API Contract Boundary

```text
Canonical Alert (Alert Schema §3)
        ↓
PostgreSQL persistence (JSONB evidence, timestamptz columns, component columns)
        ↓
API presentation (this document)
```

### What the API layer may do

| Action | Example |
|---|---|
| **Rename fields** | `detected_at` → `timestamp` |
| **Omit internal fields** | `update_count`, `dedup_identity`, `detector_output_id` |
| **Add derived/computed fields** | `src_ip` derived from `entity_key` (pair) or `alert_context` (source/destination) |
| **Convert types** | `int64` epoch µs → ISO 8601 string |

### What the API layer must not do

| Prohibition | Reason |
|---|---|
| Change canonical Alert semantics | Alert Schema is authoritative |
| Invent new threat types | BD-008 taxonomy is authoritative |
| Invent new lifecycle states | Alert Schema §10 is authoritative |
| Change detector decisions | Detector I/O is authoritative |
| Redefine dedup identity | Alert Schema §9 is authoritative |

### Status

**PROPOSED.**

---

## 4. REST API Surface

### Base path

```
/api/v1
```

Established in runtime (`API_V1_PREFIX = "/api/v1"`). Path-based versioning — breaking changes require a new prefix (e.g. `/api/v2/`).

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Service liveness check |
| `GET` | `/api/v1/alerts` | Alert list with optional filtering and pagination |
| `GET` | `/api/v1/alerts/{alert_id}` | Single alert detail |
| `GET` | `/api/v1/dashboard/summary` | Aggregate dashboard metrics |
| `WS` | `/api/v1/ws/alerts` | Live alert stream (backfill + live) |

No new endpoints are introduced in this pass.

### Status

**LOCKED.** (Approval provenance: AR-03. MVP REST endpoint contract surfaces.)

---

## 5. AlertResponse — Presentation Model

### Field definitions

| API Field | Type | Required | Source | Transformation | Notes |
|---|---|---|---|---|---|
| `alert_id` | string | Yes | `alert_id` | Direct passthrough | Unique alert identity |
| `timestamp` | string (ISO 8601) | Yes | `detected_at` (int64 µs) | int64 → ISO 8601 string | Time detector completed evaluation |
| `threat_type` | enum string | Yes | `threat_type` | Direct passthrough | 6-value BD-008 taxonomy |
| `detector_id` | enum string | Yes | `detector_id` | Direct passthrough | 5-value BD-008 taxonomy |
| `severity` | enum string | Yes | `severity` | Direct passthrough | Alert Engine's final: `critical\|high\|medium\|low\|info` |
| `confidence` | float \| null | **Yes** (field always present; value is nullable) | `confidence` | Direct passthrough; **null when absent** | [0.0, 1.0] or null; **MUST be null if canonical confidence absent — no sentinel/default substitution** |
| `src_ip` | string \| null | Optional | `entity_key` / `alert_context` | Derived; see §6 | Nullable; depends on entity_type |
| `src_port` | integer \| null | Optional | `alert_context` | Derived; see §6 | Nullable for all entity types |
| `dst_ip` | string \| null | Optional | `entity_key` / `alert_context` | Derived; see §6 | Nullable; depends on entity_type |
| `dst_port` | integer \| null | Optional | `alert_context` | Derived; see §6 | Nullable for all entity types |
| `evidence_summary` | string | Yes | `evidence_summary` | Direct passthrough | Human-readable summary |
| `status` | enum string | Yes | `status` | Direct passthrough | `new\|investigating\|closed\|false_positive` |
| `entity_type` | enum string | Yes | `entity_type` | Direct passthrough | 4-value: `source\|destination\|pair\|connection` |
| `entity_key` | string | Yes | `entity_key` | Direct passthrough | Canonical entity identifier |
| `first_seen_at` | string (ISO 8601) | Yes | `first_seen_at` (int64 µs) | int64 → ISO 8601 string | Earliest accepted detection in dedup scope |
| `last_seen_at` | string (ISO 8601) | Yes | `last_seen_at` (int64 µs) | int64 → ISO 8601 string | Most recent accepted detection in dedup scope |
| `resolved_at` | string (ISO 8601) \| null | Conditional | `resolved_at` (int64 µs) | int64 → ISO 8601 string; null if not set | Set when status transitions to terminal |

### Fields deliberately omitted from MVP API

| Omitted Field | Classification | Reason |
|---|---|---|
| `title` | Internal for MVP | `title` and `evidence_summary` have different semantic roles: `title` is a concise alert identifier; `evidence_summary` summarizes the evidence. They do not semantically replace each other. No current frontend consumer requires a separate `title` field; `evidence_summary` serves present display needs. `title` remains available in the canonical Alert for future exposure without redesign. |
| `severity_candidate` | Internal audit | Detector's severity suggestion; preserved in PostgreSQL for audit but not analyst-facing in MVP |
| `score` | System/debugging | Raw detector score; not analyst-relevant |
| `detector_output_id` | Internal plumbing | Internal DetectorOutput reference |
| `update_count` | Internal concurrency | Alert Engine concurrency signal; not analyst-facing |
| `dedup_identity` | Internal | Represented by component columns; not analyst-facing |
| `source_feature_references` | Internal provenance | Future debug/detail endpoint concern |
| `detector_version` / `model_version` | System/debugging | MVP omit; may be added to a future analyst-optional detail view |
| `schema_version` | Internal contract | Not analyst-facing |
| `evidence` (structured JSONB) | Internal/partial | `evidence_summary` serves MVP display; structured exposure is OPEN for future detail endpoint |
| `alert_context` internals | Internal | Used to derive `src_ip`/`dst_ip`/ports; not exposed raw |

### `confidence` null rule

When the upstream `DetectorOutput` does not carry a `confidence` value (i.e., canonical `confidence` is absent), the API response **MUST** return `confidence: null`. It **MUST NOT** substitute `0`, `-1`, or any other sentinel or default value. Substituting a sentinel would misrepresent the detector's output to the analyst.

### `title` note

`title` is omitted from the MVP API for the reasons stated above. This is a deliberate presentation-layer decision. If future frontend or consumer requirements emerge that need a concise per-alert identifier distinct from `evidence_summary`, `title` can be added to the API response without any upstream redesign.

### Status

**LOCKED.** (Approval provenance: AR-03. Structural schema, ISO 8601 presentation, confidence nullability.)

---

## 6. Entity Presentation Model

### Four entity types — mapped separately

Alert Schema §14 defines exactly 4 `entity_type` values. The API derives IP/port presentation differently for each.

| entity_type | `src_ip` | `dst_ip` | `src_port` | `dst_port` |
|---|---|---|---|---|
| `source` | = `entity_key` (source IP) | From `alert_context` if captured at alert-creation time, else **null** | From `alert_context`, else **null** | From `alert_context`, else **null** |
| `destination` | From `alert_context` if captured, else **null** | = `entity_key` (destination IP) | From `alert_context`, else **null** | From `alert_context`, else **null** |
| `pair` | Parsed from `entity_key`: left of `\|` separator | Parsed from `entity_key`: right of `\|` separator | From `alert_context`, else **null** | From `alert_context`, else **null** |
| `connection` | **null** — connection identifier is not an IP; not derivable | **null** | **null** | **null** |

### Key principles

- **`entity_type` and `entity_key` are always included** as canonical fields. They are never omitted from the API response.
- **IP/port fields are always nullable.** No entity type guarantees all four are non-null.
- **`alert_context` is internal.** The API derives presentation fields from it but does not expose `alert_context` raw.
- **Do not generalize `source`/`destination` handling to `connection`.** This type uses opaque identifiers and cannot yield IP presentation without explicit `alert_context` capture.

### Source of IP/port context for `source`/`destination`/`pair`

Per PostgreSQL Schema §3, the Alert Engine captures representative entity context in `alert_context` JSONB at alert-creation time for cases where the "other side" of the entity is not in `entity_key`. Exact `alert_context` field names are **OPEN**. The API layer reads whatever the Alert Engine has stored there; if absent, the presentation field is null.

### Status

**LOCKED.** (Approval provenance: AR-03. Entity presentation rules.)

---

## 7. Internal vs External Fields

### Classification table

| Field | Classification | API exposure |
|---|---|---|
| `alert_id` | Analyst-facing | Yes |
| `timestamp` (= `detected_at`) | Analyst-facing | Yes |
| `threat_type` | Analyst-facing | Yes |
| `detector_id` | Analyst-facing | Yes |
| `severity` | Analyst-facing | Yes |
| `confidence` | Analyst-facing | Yes (nullable) |
| `src_ip` / `dst_ip` | Analyst-facing | Yes (derived, nullable) |
| `src_port` / `dst_port` | Analyst-facing | Yes (derived, nullable) |
| `evidence_summary` | Analyst-facing | Yes |
| `status` | Analyst-facing | Yes |
| `entity_type` | Analyst-facing | Yes |
| `entity_key` | Analyst-facing | Yes |
| `first_seen_at` / `last_seen_at` | Analyst-facing | Yes |
| `resolved_at` | Analyst-facing | Yes (nullable) |
| `title` | Internal for MVP | No — deliberate omission (see §5) |
| `severity_candidate` | Internal audit | No |
| `score` | System/debugging | No |
| `detector_output_id` | Internal plumbing | No |
| `update_count` | Internal concurrency | No |
| `dedup_identity` | Internal | No |
| `source_feature_references` | Internal provenance | No |
| `detector_version` / `model_version` | System/debugging | No (MVP) |
| `schema_version` | Internal contract | No |
| `evidence` (structured) | Internal/partial | No (MVP) |
| `alert_context` | Internal | No (derived from) |

---

## 8. Alert List Endpoint

### `GET /api/v1/alerts`

**Purpose:** Return a filtered, paginated list of alerts.

**Current implementation:** Returns all alerts with no filtering or pagination (12 static mock records).

**Final contract — query parameters (PROPOSED):**

| Parameter | Type | Description | Default |
|---|---|---|---|
| `status` | enum string | Filter: `new\|investigating\|closed\|false_positive` | All statuses |
| `severity` | enum string | Filter: `critical\|high\|medium\|low\|info` | All severities |
| `threat_type` | enum string | Filter by threat type | All threat types |
| `detector_id` | enum string | Filter by detector | All detectors |
| `entity_type` | enum string | Filter by entity type | All entity types |
| `entity_key` | string | Exact match on entity key | No filter |
| `since` | ISO 8601 string | `detected_at ≥ since` | No lower bound |
| `until` | ISO 8601 string | `detected_at ≤ until` | No upper bound |
| `limit` | integer | Maximum alerts to return | **OPEN** |
| `offset` | integer | Pagination offset | 0 |
| `order` | string | Sort order | `detected_at_desc` |

**Response model:**

```json
{
  "alerts": [ AlertResponse, ... ],
  "total": integer
}
```

`total` = total matching alerts (ignoring pagination), enabling frontend page count.

**Error cases:**
- `422` — invalid enum value for filter parameters
- `422` — invalid pagination values (e.g. negative `offset`)

### Status

**LOCKED.** (Approval provenance: AR-03. Endpoint surface). **OPEN** (pagination limits, exact filters).

---

## 9. Pagination

### Model: limit + offset

**Rationale:** Simplest viable for MVP. Cursor pagination deferred — requires stable authoritative ordering guarantee which is OPEN at the DetectorOutput level (Detector I/O §13).

**Structure:** `limit` and `offset` query parameters. `total` in response for page count computation.

**Exact defaults/limits:** **OPEN.** Implementation will determine sensible defaults based on operational alert volumes.

---

## 10. Sorting / Ordering

**Default:** `detected_at DESC` — most recent detection first.

This is a presentation/query behavior decision. It does not imply `detected_at` provides authoritative ordering at the DetectorOutput level (it does not — Detector I/O §13: `evaluated_at` is an observability field, not a guaranteed monotonic ordering signal). For API presentation and dashboard use, `detected_at DESC` is appropriate and analyst-useful.

**Supported order values (PROPOSED):** `detected_at_desc` (default), `detected_at_asc`.

Additional ordering options (e.g. by severity, by `created_at`): **OPEN**.

---

## 11. Single Alert Detail

### `GET /api/v1/alerts/{alert_id}`

**Purpose:** Return a single alert by its unique `alert_id`.

**Path parameter:** `alert_id` — the canonical alert identity.

**Response:** Full `AlertResponse` (same model as list items — see §5).

**No separate DTO:** Single and list responses use the same model for MVP. A future detail-only endpoint exposing structured `evidence` JSONB or provenance references would be a v2 concern.

**Error cases:**
- `404` — alert not found: `{"detail": "Alert not found"}`
- `400` — malformed `alert_id` format: PROPOSED `{"detail": "Invalid alert_id format"}`


### Status

**LOCKED.** (Approval provenance: AR-03)
---

## 12. Dashboard Contract

### `GET /api/v1/dashboard/summary`

**Purpose:** Aggregate metrics for the SOC dashboard overview.

**Response model — `DashboardSummaryResponse`:**

| Field | Type | Required | Source | Notes |
|---|---|---|---|---|
| `total_alerts` | integer | Yes | PostgreSQL COUNT | Total alert count |
| `critical_count` | integer | Yes | Severity breakdown | Count where severity = critical |
| `high_count` | integer | Yes | Severity breakdown | Count where severity = high |
| `medium_count` | integer | Yes | Severity breakdown | Count where severity = medium |
| `low_count` | integer | Yes | Severity breakdown | Count where severity = low |
| `info_count` | integer | Yes | Severity breakdown | Count where severity = info |
| `by_threat_type` | dict[string, int] | Yes | Threat type breakdown | `{threat_type: count}` |
| `by_detector` | dict[string, int] | Yes | Detector breakdown | `{detector_id: count}` |
| `recent_alerts` | AlertResponse[] | Yes | Top-N recent alerts | Ordered by `detected_at DESC`; count: **OPEN** (mock uses 5) |

**Production note:** The real implementation will use PostgreSQL aggregation queries. Redis hot state (BD-004) may serve pre-aggregated metrics for performance. The mock implementation (`MockDashboardService`) derives all fields from in-memory `Counter` over `MOCK_ALERTS` and `recent_alerts = alerts[:5]`.

**Explicit note on dashboard fields:** All fields in `DashboardSummaryResponse` are presentation conveniences derived from the canonical Alert data. They are not separate canonical data entities. `by_threat_type` and `by_detector` use the BD-008 Active taxonomy string values as keys.

### Status

**LOCKED.** (Approval provenance: AR-03)

---

## 13. Health Contract

### `GET /api/v1/health`

**Purpose:** Service liveness check.

**Response model — `HealthResponse`:**

```json
{
  "status": "ok"
}
```

| Field | Type | Required | Value |
|---|---|---|---|
| `status` | string | Yes | `"ok"` when service is up |

**Scope:** MVP liveness only. No dependency status fields (PostgreSQL connectivity, Redis, Redpanda) — those infrastructure components are not yet implemented. Dependency health checking is a production infrastructure concern and is not finalized here.

### Status

**LOCKED.** (Approval provenance: AR-03)

---

## 14. WebSocket Contract

### `WS /api/v1/ws/alerts`

**Purpose:** Live alert delivery — backfill of recent alerts on connect, then streaming of new alerts as they are published.

**Connection URL pattern:**
```
ws://<host>/api/v1/ws/alerts
wss://<host>/api/v1/ws/alerts  (TLS)
```

### Protocol sequence

```text
Client connects
        ↓
Server sends N backfill alerts (type: "backfill")
        ↓
Server sends backfill_complete marker (alert: null)
        ↓
Server enters live mode → sends new alerts (type: "live")
```

### Backfill behavior

- Server sends the N most recent alerts as `backfill` messages
- N is a configurable server constant (`WS_BACKFILL_COUNT = 5` in current dummy)
- Exact production N: **OPEN**
- Backfill alerts follow the same `AlertResponse` model as REST
- After all backfill messages, server sends exactly one `backfill_complete` message

### Live alert behavior

**In production:** Live alerts are delivered after Redis Pub/Sub notification, which is triggered only after the corresponding PostgreSQL operation has committed.

- For **INSERT** (new alert): commit-before-publish invariant is **LOCKED** (BD-005)
- For **UPDATE** (alert update): commit-before-publish invariant is **PROPOSED** (Alert Schema §4)

Do not treat the UPDATE extension as LOCKED.

**In current dummy:** Server emits a live alert every `WS_LIVE_INTERVAL_SECONDS = 4.0` seconds, capped at `WS_LIVE_MAX_ALERTS = 50`, then stops. This is a simulation only.

### Error behavior

- Unhandled server errors: server closes with WebSocket code `1011`
- Client reconnect: client-side responsibility (not a server contract)
  - Current frontend: 3s delay, max 10 reconnect attempts
- No server-initiated disconnect message type is defined

### Heartbeat

None currently defined. **OPEN.**

### Authentication

Not defined in this pass. **OPEN.**


### Status

**LOCKED.** (Approval provenance: AR-03. WebSocket envelope/backfill semantics)
---

## 15. WebSocket Message Model

### `WebSocketMessage`

```json
{
  "type": "backfill" | "live" | "backfill_complete",
  "alert": AlertResponse | null
}
```

| Field | Type | Notes |
|---|---|---|
| `type` | string enum | `backfill`, `live`, or `backfill_complete` |
| `alert` | AlertResponse \| null | Full AlertResponse for `backfill`/`live`; **null** for `backfill_complete` |

This is the smallest structure compatible with the existing frontend. No second alert model is introduced. REST and WebSocket share the same `AlertResponse` model.

### Status

**LOCKED.** (Approval provenance: AR-03)

---

## 16. PostgreSQL → API Mapping

### Three-layer translation

```text
Canonical Alert field (Alert Schema)
        ↓
PostgreSQL column/JSONB (PostgreSQL Schema §5/§9)
        ↓
API field (this document)
```

| Canonical Alert Field | PostgreSQL Representation | API Field | Transformation |
|---|---|---|---|
| `alert_id` | UUID column | `alert_id` | Direct |
| `detected_at` (int64 µs) | `timestamptz` column | `timestamp` | Rename + int64→ISO 8601 |
| `threat_type` | text enum column | `threat_type` | Direct |
| `detector_id` | text enum column | `detector_id` | Direct |
| `entity_type` | text enum column | `entity_type` | Direct |
| `entity_key` | text column | `entity_key` | Direct |
| `first_seen_at` (int64 µs) | `timestamptz` column | `first_seen_at` | int64→ISO 8601 |
| `last_seen_at` (int64 µs) | `timestamptz` column | `last_seen_at` | int64→ISO 8601 |
| `created_at` (int64 µs) | `timestamptz` column | — | **Not exposed in MVP** |
| `status` | text enum column | `status` | Direct |
| `severity` | text enum column | `severity` | Direct |
| `severity_candidate` | text enum column | — | **Not exposed** |
| `confidence` | float column (nullable) | `confidence` | Direct; null when column is null |
| `score` | float column (nullable) | — | **Not exposed** |
| `evidence_summary` | text column | `evidence_summary` | Direct |
| `evidence` (JSONB) | JSONB column | — | Not exposed raw; `alert_context` sub-field used to derive `src_ip`/`dst_ip`/ports |
| `alert_context` (inside evidence JSONB) | JSONB sub-field | `src_ip`, `dst_ip`, `src_port`, `dst_port` | Derived per entity_type (see §6) |
| `entity_key` (pair type) | text column | `src_ip`, `dst_ip` | Parsed: left/right of `\|` |
| `resolved_at` (int64 µs) | `timestamptz` column (nullable) | `resolved_at` | int64→ISO 8601; null when column is null |
| `source_feature_references` (JSONB) | JSONB column | — | **Not exposed** |
| `detector_version` | text column | — | **Not exposed (MVP)** |
| `model_version` | text column (nullable) | — | **Not exposed (MVP)** |
| `schema_version` | text column | — | **Not exposed** |
| `detector_output_id` | UUID/text column | — | **Not exposed** |
| `update_count` | integer column | — | **Not exposed** |
| `dedup_digest` | text column (optional) | — | **Not exposed** |
| `title` | text column | — | **Not exposed in MVP** (deliberate; see §5) |

### Key principle

PostgreSQL storage choices do not automatically dictate API field exposure. The API layer makes independent presentation decisions based on what is analyst-useful.

---

## 17. Error Model

### Structural error response

```json
{
  "detail": "Human-readable error message"
}
```

All errors use the same top-level `detail` field (FastAPI standard).

### Error cases

| HTTP Status | Trigger | Response body |
|---|---|---|
| `404 Not Found` | Alert not found | `{"detail": "Alert not found"}` |
| `422 Unprocessable Entity` | Invalid query parameter (enum value, type mismatch) | FastAPI/Pydantic validation error structure |
| `422 Unprocessable Entity` | Invalid pagination values (e.g. negative offset) | FastAPI/Pydantic validation error structure |
| `400 Bad Request` | Malformed `alert_id` identifier | PROPOSED: `{"detail": "Invalid alert_id format"}` |
| `500 Internal Server Error` | Server/persistence failure | PROPOSED: `{"detail": "Internal server error"}` |

Exact error message wording: **OPEN** (except the existing `"Alert not found"` which is retained from the current implementation).

---

## 18. Alert Lifecycle Compatibility

### Lifecycle enum

```
new | investigating | closed | false_positive
```

These are the only valid `status` values. The API must not introduce:
- `open`
- `acknowledged`
- `resolved`
- `dismissed`

or any other synonym unless an upstream approved change exists.

### DetectorOutput.decision ≠ Alert.status

This distinction is **preserved explicitly**:
- `DetectorOutput.decision` is the detector's evaluation outcome (Detector I/O §16): `no_threat`, `detection`, `insufficient_data`, `invalid_input`, `detector_error`
- `Alert.status` is the analyst's workflow state, starting at `new` regardless of confidence
- Only `decision = detection` produces alerts. `Alert.status` begins at `new` and transitions only via analyst action

### "Closed" semantics

"Closed" is an analyst workflow status. It does **not** imply Irochi mitigated or stopped the threat. Irochi is a passive detection/intelligence system.

---

## 19. Threat / Detector Taxonomy

BD-008 taxonomy inherited as **Active** (not promoted to Locked):

| Detector IDs (5) | Threat Types (6) |
|---|---|
| `ddos_detector` | `volumetric_ddos` |
| `recon_detector` | `c2_beaconing` |
| `dns_dga_tunnel_detector` | `dga_dns_tunnel` |
| `tls_c2_detector` | `encrypted_malware` |
| `exfiltration_detector` | `recon_portscan` |
| | `data_exfiltration` |

The API uses these values as-is. No API-specific detector IDs or threat names are created. `detector_id` and `threat_type` are **distinct fields** — one detector may emit multiple threat types.

---

## 20. API Versioning

### Current version

```
/api/v1/
```

Established in the current API scaffold (`API_V1_PREFIX = "/api/v1"`).

### Versioning model

- **Path-based versioning:** `/api/v1/`, `/api/v2/` when breaking changes require it
- **Schema version:** `schema_version` exists in the canonical Alert (Alert Schema §20) but is not exposed in the MVP API response. API version is conveyed by the path prefix.
- **Backward compatibility:** Non-breaking additions (new optional response fields) do not require a version bump. Breaking changes (removing fields, changing types) require a new version prefix.
- **v2 migration:** **OPEN** — no concrete requirement exists yet.

### Status

**PROPOSED.**

---

## 21. Caching / Real-Time Presentation

### REST (PostgreSQL-backed)

REST endpoints read from PostgreSQL. No caching layer is defined in this pass.

### WebSocket (Redis Pub/Sub-driven)

Live alert WebSocket delivery in production is driven by Redis Pub/Sub, which is triggered only after the corresponding PostgreSQL operation has committed:

- **INSERT** (new alert): commit-before-publish = **LOCKED** (BD-005)
- **UPDATE** (alert update): commit-before-publish = **PROPOSED** (Alert Schema §4)

Redis is **not** a source of truth (BD-004). Redis Pub/Sub is the fan-out mechanism; PostgreSQL is the durable alert store. No Redis channel/topic is designed in this document.

---

## 22. Frontend Compatibility

### Field-by-field compatibility analysis

| Frontend field (`types/index.ts`) | API response field | Compatibility |
|---|---|---|
| `alert_id: string` | `alert_id: string` | ✅ Unchanged |
| `timestamp: string` | `timestamp: string` (ISO 8601) | ✅ Unchanged |
| `threat_type: ThreatType` | `threat_type: string enum` | ✅ Unchanged |
| `detector_id: DetectorId` | `detector_id: string enum` | ✅ Unchanged |
| `severity: Severity` | `severity: string enum` | ✅ Unchanged |
| `confidence: number` | `confidence: float \| null` | ⚠️ **Soft breaking**: frontend type must migrate from `number` to `number \| null` when real implementation arrives |
| `src_ip: string \| null` | `src_ip: string \| null` | ✅ Unchanged |
| `src_port: number \| null` | `src_port: integer \| null` | ✅ Compatible |
| `dst_ip: string \| null` | `dst_ip: string \| null` | ✅ Unchanged |
| `dst_port: number \| null` | `dst_port: integer \| null` | ✅ Compatible |
| `evidence_summary: string` | `evidence_summary: string` | ✅ Unchanged |
| `status: AlertStatus` | `status: string enum` | ✅ Unchanged |
| — | `entity_type` (new) | ✅ Additive — frontend can ignore |
| — | `entity_key` (new) | ✅ Additive — frontend can ignore |
| — | `first_seen_at` (new) | ✅ Additive — frontend can ignore |
| — | `last_seen_at` (new) | ✅ Additive — frontend can ignore |
| — | `resolved_at` (new) | ✅ Additive — frontend can ignore |

### Dashboard compatibility

| Frontend field | API field | Compatibility |
|---|---|---|
| `total_alerts: number` | `total_alerts: integer` | ✅ Unchanged |
| `critical_count` ... `info_count: number` | Same | ✅ Unchanged |
| `by_threat_type: Record<string, number>` | Same | ✅ Unchanged |
| `by_detector: Record<string, number>` | Same | ✅ Unchanged |
| `recent_alerts: Alert[]` | `recent_alerts: AlertResponse[]` | ✅ Compatible |

### WebSocket compatibility

Frontend `WsMessage` interface expects `{type: WsMessageType, alert: Alert | null}`. API WebSocket message model is identical in structure.

### Summary

- **One soft breaking change:** `confidence` becomes nullable. Frontend type update required when real implementation is deployed. **No frontend code changes in this pass.**
- **Five additive fields:** All backward-compatible; frontend can safely ignore.
- **Dashboard and WebSocket:** Fully compatible.

---

## 23. Complete API Field Tables

### AlertResponse — complete field table

| Field | Type | Required | Canonical Source | PostgreSQL Source | Transformation | Consumer |
|---|---|---|---|---|---|---|
| `alert_id` | string | Yes | `alert_id` | UUID column | Direct | Frontend, analysts |
| `timestamp` | string (ISO 8601) | Yes | `detected_at` | `detected_at` timestamptz | int64→ISO 8601 | Frontend, analysts |
| `threat_type` | string enum | Yes | `threat_type` | text column | Direct | Frontend, analysts |
| `detector_id` | string enum | Yes | `detector_id` | text column | Direct | Frontend, analysts |
| `severity` | string enum | Yes | `severity` | text column | Direct | Frontend, analysts |
| `confidence` | float \| null | **Yes** (value nullable) | `confidence` | float column (nullable) | Direct; **null when column is null; no sentinel substitution** | Frontend, analysts |
| `src_ip` | string \| null | Optional | `entity_key` / `alert_context` | Derived | See §6 | Frontend, analysts |
| `src_port` | integer \| null | Optional | `alert_context` | Derived | See §6 | Frontend, analysts |
| `dst_ip` | string \| null | Optional | `entity_key` / `alert_context` | Derived | See §6 | Frontend, analysts |
| `dst_port` | integer \| null | Optional | `alert_context` | Derived | See §6 | Frontend, analysts |
| `evidence_summary` | string | Yes | `evidence_summary` | text column | Direct | Frontend, analysts |
| `status` | string enum | Yes | `status` | text column | Direct | Frontend, analysts |
| `entity_type` | string enum | Yes | `entity_type` | text column | Direct | Frontend, analysts |
| `entity_key` | string | Yes | `entity_key` | text column | Direct | Frontend, analysts |
| `first_seen_at` | string (ISO 8601) | Yes | `first_seen_at` | timestamptz column | int64→ISO 8601 | Analysts |
| `last_seen_at` | string (ISO 8601) | Yes | `last_seen_at` | timestamptz column | int64→ISO 8601 | Analysts |
| `resolved_at` | string (ISO 8601) \| null | Conditional | `resolved_at` | timestamptz column (nullable) | int64→ISO 8601; null if absent | Analysts |

### AlertListResponse

| Field | Type | Required | Source |
|---|---|---|---|
| `alerts` | AlertResponse[] | Yes | PostgreSQL query result |
| `total` | integer | Yes | PostgreSQL COUNT of matching records |

### DashboardSummaryResponse

| Field | Type | Required | Source |
|---|---|---|---|
| `total_alerts` | integer | Yes | COUNT(*) |
| `critical_count` | integer | Yes | Severity COUNT |
| `high_count` | integer | Yes | Severity COUNT |
| `medium_count` | integer | Yes | Severity COUNT |
| `low_count` | integer | Yes | Severity COUNT |
| `info_count` | integer | Yes | Severity COUNT |
| `by_threat_type` | dict[string, int] | Yes | Grouped COUNT by threat_type |
| `by_detector` | dict[string, int] | Yes | Grouped COUNT by detector_id |
| `recent_alerts` | AlertResponse[] | Yes | Top-N by `detected_at DESC` |

### HealthResponse

| Field | Type | Required | Value |
|---|---|---|---|
| `status` | string | Yes | `"ok"` |

### WebSocketMessage

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | string enum | Yes | `backfill` \| `live` \| `backfill_complete` |
| `alert` | AlertResponse \| null | Yes | null only for `backfill_complete` |

---

## 24. Status Discipline Summary

| Item | Status |
|---|---|
| PostgreSQL is durable alert truth | **LOCKED** (BD-003) |
| Redis hot state and Pub/Sub are separate roles | **LOCKED** (BD-004) |
| PostgreSQL INSERT commit-before-publish | **LOCKED** (BD-005) |
| PostgreSQL UPDATE commit-before-publish | **PROPOSED** (Alert Schema §4) |
| Alert Schema is canonical application-level contract | **Inherited PROPOSED** |
| PostgreSQL is persistence source | **Inherited PROPOSED** |
| Existing endpoint purposes and REST surface | **Inherited PROPOSED** |
| `/api/v1/` versioned prefix | **Inherited PROPOSED** |
| Alert presentation field set | **PROPOSED** |
| AlertResponse field mapping | **PROPOSED** |
| `confidence: null` rule | **PROPOSED** |
| `title` deliberate MVP omission | **PROPOSED** |
| Entity presentation model (5 types) | **PROPOSED** |
| Dashboard response structure | **PROPOSED** |
| WebSocket message model | **PROPOSED** |
| Filtering/pagination structure | **PROPOSED** |
| Error response structure | **PROPOSED** |
| API versioning model | **PROPOSED** |
| BD-008 detector/threat taxonomy | **Inherited Active / not LOCKED** |
| `detector_id ≠ threat_type` | **Inherited Active** |
| Exact pagination defaults/limits | **OPEN** |
| Exact filter combinations | **OPEN** |
| Exact error body wording (except 404) | **OPEN** |
| WebSocket heartbeat/reconnect policy | **OPEN** |
| Authentication/authorization | **OPEN** |
| Rate limiting | **OPEN** |
| Caching policy | **OPEN** |
| Future API v2 migration strategy | **OPEN** |
| Exact exposure of structured evidence/provenance | **OPEN** |
| Deployment-specific gateway configuration | **OPEN** |
| `title` exposure in future versions | **OPEN** |
| Recent alerts top-N count (production) | **OPEN** |
| Exact `alert_context` entity-context field names | **OPEN** (inherited from PostgreSQL Schema §3) |

---

## 25. Review Checklist

- [x] PHASE 0 verification checkpoint produced and approved before this document was written
- [x] PHASE 1 implementation plan produced, reviewed, corrected, and approved before this document was written
- [x] Alert Schema v1 used as canonical source
- [x] PostgreSQL Schema v1 used as persistence source
- [x] Current REST endpoints verified against routes and service implementations
- [x] Current WebSocket verified against `websocket/alerts.py`, `alert_service.py`, and `core/config.py`
- [x] AlertResponse mapping defined — all canonical Alert fields classified for exposure/omission
- [x] `entity_type` 4-value model preserved; each entity type mapped separately (§6)
- [x] API presentation does not redefine canonical alert identity
- [x] `detector_id ≠ threat_type` preserved (§19)
- [x] Lifecycle enum preserved — `new|investigating|closed|false_positive` only (§18)
- [x] `DetectorOutput.decision ≠ Alert.status` preserved (§18)
- [x] REST/WS boundary defined — same `AlertResponse` model, separate channels (§14–§15)
- [x] Frontend compatibility checked field-by-field (§22)
- [x] Filtering/pagination documented (§8–§10)
- [x] Error model documented (§17)
- [x] API versioning documented (§20)
- [x] Redis source-of-truth separation preserved (BD-004, §21)
- [x] INSERT=LOCKED, UPDATE=PROPOSED preserved for commit-before-publish (§14, §21)
- [x] `confidence: null` rule documented — no sentinel substitution (§5)
- [x] `title` deliberate MVP omission documented with reasoning (§5)
- [x] Design Contracts vs Pending distinction preserved in BACKEND_CONTEXT.md (Task 26)
- [x] No runtime code changed
- [x] No frontend code changed
- [x] No implementation infrastructure changed
- [x] No SQL or ORM changes
- [x] Nothing staged, committed, or pushed

---

## 26. Cross-Document Consistency

| Document | Compatibility status |
|---|---|
| ALERT_SCHEMA_DRAFT_v1.md §3 | **Compatible.** All 25 canonical Alert fields accounted for; presented, omitted, or derived fields documented explicitly. |
| ALERT_SCHEMA_DRAFT_v1.md §9 (dedup) | **Compatible.** Dedup fields not exposed in API; internal only. |
| ALERT_SCHEMA_DRAFT_v1.md §10 (lifecycle) | **Compatible.** Lifecycle enum preserved exactly. |
| ALERT_SCHEMA_DRAFT_v1.md §14 (entity types) | **Compatible.** 4-value entity_type from §14 used throughout. |
| ALERT_SCHEMA_DRAFT_v1.md §16 (API boundary) | **Compatible.** This document implements §16's stated boundary. |
| POSTGRESQL_SCHEMA_DRAFT_v1.md §3 (entity context) | **Compatible.** `alert_context` JSONB used to derive IP/port presentation; raw `alert_context` not exposed. |
| POSTGRESQL_SCHEMA_DRAFT_v1.md §5 (columns) | **Compatible.** Timestamptz → ISO 8601 conversion documented. |
| POSTGRESQL_SCHEMA_DRAFT_v1.md §18 (API boundary) | **Compatible.** This document is the defined downstream. |
| DETECTOR_IO_CONTRACT_DRAFT_v1.md §13 (revision) | **Compatible.** No `revision` naming in API fields. |
| BACKEND_DECISIONS.md BD-003/004/005 | **Compatible.** All statuses preserved exactly. |
| BACKEND_DECISIONS.md BD-008 | **Compatible.** Active, not Locked. |
| alerts.py / dashboard.py / health.py | **Compatible.** No runtime changes; this document formalizes the contract those models will eventually implement. |
| API_CONTRACT.md | **Compatible.** Historical dummy contract preserved; now points to this document. |
| DATA_CONTRACTS.md | **Compatible.** Item 7 added (Final API Contract DRAFT / IN PROGRESS). |
| frontend/src/types/index.ts | **Compatible.** One soft breaking change (`confidence` nullable) identified and documented; no frontend changes in this pass. |
| frontend/src/services/websocket.ts | **Compatible.** WebSocket message structure unchanged. |

### Resolved contradictions from PHASE 0

| ID | Finding | Resolution |
|---|---|---|
| C-1 | `src_port`/`dst_port` in runtime model but missing from API_CONTRACT.md example JSON | Explicitly added to this document's AlertResponse definition |
| C-2 | Canonical `confidence` is Conditional; runtime model makes it required | Resolved: API makes `confidence: float \| null`; null when absent; no sentinel substitution |
| C-3 | Canonical `detected_at` is int64 µs; frontend expects ISO 8601 string | Resolved: API layer converts int64 → ISO 8601; field renamed to `timestamp` |

---

## 27. Next Design Step

```text
API Contract (Draft v1)     ← THIS DOCUMENT
        ↓
Implementation Phase
  - PostgreSQL real implementation
  - Redis integration
  - Real Alert Engine
  - FastAPI route/model updates to match this contract
  - Frontend type migration (confidence: number | null)
```

This is the last design-chain document before production implementation begins.

---

## 28. Final Status

**DRAFT v1 — API presentation contract complete.**

This revision defines the full AlertResponse model (17 fields, 3 derived, 14 internal-omitted), entity presentation for all 5 entity types, dashboard contract, health contract, WebSocket protocol with INSERT/UPDATE commit ordering status, pagination model, error model, API versioning, and frontend compatibility analysis.

All structural definitions are **PROPOSED**. Implementation-specific details (exact pagination defaults, error wording, heartbeat, authentication, caching) are **OPEN**.

This document must not be marked FINAL until explicitly approved and all OPEN items are resolved or explicitly deferred to implementation.
