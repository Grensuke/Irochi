# Irochi — Implementation Brief: Cross-Detector Risk Fusion, Early-Warning, Unknown-Threat Anomaly Detection & Forensic Replay

You are working inside the existing **Irochi** repository (SIH26145 — passive network intrusion detection). Before writing any code, read the files referenced in each section below so your implementation matches the existing conventions exactly (naming, docstring style, error-handling patterns, "OPEN/DEVELOPMENT CONFIG" comment style for undecided parameters). Do not restructure or rewrite anything outside the scope of this brief.

## 0. What already exists (don't rebuild these)

- 5 active detectors (`DDoS`, `Recon`, `DNS/DGA`, `TLS/C2`, `Exfiltration`) implementing `BaseDetector`, registered in `DetectorRegistry`, routed by `DetectorRouter` (`backend/app/services/detectors/`).
- `AlertEngine` (`backend/app/services/alert_engine.py`) persists `DetectorOutput`s into the `alerts` Postgres table and publishes to Redis pub/sub.
- `DetectionPipeline` (`backend/app/services/pipeline.py`) is the orchestrator: feature extraction → `router.route(record)` → for each `DetectorOutput`, opens a DB session and calls `alert_engine.process_detector_output(output)`.
- Per-alert **evidence** already exists and is real: `evidence.signals` (value/threshold/triggered), DGA `probability`/`threshold`/`features_used`. Frontend `utils/explanation.ts` turns this into prose. **Do not touch this — it stays as-is.**
- Frontend already has client-side correlation (`utils/correlation.ts`, `utils/progression.ts`) and a working replay UI on `AlertDetailPage.tsx` (Play/Pause/Prev/Next stepping through a client-computed timeline every 2.5s) plus `NarrativePanel.tsx` calling the real `/api/v1/narrative/generate` endpoint. **Keep all of this working as a fallback path** for whenever a backend Incident isn't available (e.g. an alert predating this change).
- Two enum definitions for `ThreatType`/`DetectorId` exist **in parallel** and must be kept in sync: `backend/app/schemas/detectors.py` (internal detector plumbing) and `backend/app/schemas/alerts.py` (API presentation). The frontend has its own third copy in `frontend/src/types/index.ts`. Any new enum value goes in **all three places**.

## 1. Scope

Build, as one connected feature set:

1. **Cross-Detector Risk Fusion** — a real, persisted, weighted fusion score per correlated cluster of alerts (not a naive sum).
2. **Early-Warning / Attack Progression** — a Normal→Anomaly→Suspicious→Likely Attack→Confirmed Attack ladder, plus a "current stage / likely next stage" forecast, derived from the same cluster.
3. **Unknown-Threat Anomaly Detection** — a 6th, statistical baseline-deviation detector that fires when none of the 5 named detectors match but an entity's behavior deviates sharply from its own recent history.
4. **Attack Replay / Forensic Timeline** — upgrade the existing replay UI to step through the *persisted* incident timeline with a visible evidence chain per step, instead of the ad hoc client-side grouping.
5. **Security Posture Score** (small, do last) — one composite number + category breakdown on `Overview.tsx`, fed by the new incidents.
6. **Cleanup** — resolve the `Investigation.tsx` vs `AlertDetailPage.tsx` duplication (see §5).

The unifying concept behind 1–4 is a new backend-persisted **`Incident`**: a cluster of correlated alerts for one entity, with a fused score, a stage, and a forecast attached. Build this once; everything else reads from it.

## 2. Architectural decisions (do not deviate without a good reason — these were chosen deliberately)

### 2.1 Incident correlation key
Correlate by the alert's derived `src_ip` (same logic `AlertResponse.from_orm` already uses to pull `src_ip` out of `entity_key`/`evidence.alert_context`), within a rolling **60-minute** window — this matches the existing frontend `CORRELATION_WINDOW_MS` in `correlation.ts`, so behavior stays consistent whether the backend or the fallback path is active.

### 2.2 Weighted risk fusion (NOT a naive sum)
```
BASE_WEIGHT = {
  "recon_portscan":    15,
  "dga_dns_tunnel":     20,
  "c2_beaconing":       22,
  "encrypted_malware":  20,
  "data_exfiltration":  25,
  "volumetric_ddos":    18,
  "novel_anomaly":      12,
}

contribution[threat_type] = BASE_WEIGHT[threat_type] * max(confidence of that threat_type's alerts in this incident)
raw_score      = sum(contribution.values())
distinct_types = number of distinct threat_types present in the incident
escalation     = 1 + 0.15 * max(0, distinct_types - 1)
risk_score     = min(100, round(raw_score * escalation))
```
Persist `risk_breakdown` as the per-threat-type `contribution` dict so the UI can render the doc's "Recon +15 / DGA +17 / … = 91" table directly. Mark `BASE_WEIGHT` and the `0.15` escalation constant with an `# OPEN / UNVALIDATED — tune during evaluation` comment, matching the existing style in `detectors/recon.py` and `detectors/ddos.py`.

### 2.3 Early-warning stage ladder
```
KILL_CHAIN_ORDER = ["recon_portscan", "dga_dns_tunnel", "c2_beaconing", "encrypted_malware", "data_exfiltration"]
```
- Only `novel_anomaly` present → `stage_state = "anomaly"`
- 1 distinct kill-chain type present → `"suspicious"`
- 2 distinct kill-chain types present → `"likely_attack"`
- 3+ distinct kill-chain types present, OR `data_exfiltration` present at all → `"confirmed_attack"`
- `volumetric_ddos` is handled separately (it isn't a kill-chain precursor): map it to `"likely_attack"` if severity is high/critical, else `"suspicious"`.
- `current_stage` = the most-advanced distinct kill-chain type present (last match in `KILL_CHAIN_ORDER`), or `"volumetric_ddos"` / `"novel_anomaly"` if that's all that's present.

### 2.4 Attack forecast
```
KILL_CHAIN_NEXT = {
  "recon_portscan":   "dga_dns_tunnel",
  "dga_dns_tunnel":   "c2_beaconing",
  "c2_beaconing":     "encrypted_malware",
  "encrypted_malware":"data_exfiltration",
  "data_exfiltration": None,
}
forecast_next_stage = KILL_CHAIN_NEXT.get(current_stage)   # None for ddos/anomaly/exfiltration
```
Always attach a fixed `forecast_note`: *"This is a risk forecast based on observed kill-chain progression, not a claim that the next stage has occurred."* Surface this note anywhere the forecast is shown in the UI — this disclaimer is a hard requirement, not optional copy.

### 2.5 Unknown-threat anomaly detector — statistical baseline-deviation
No trained model. Use an online per-entity, per-signal baseline via **Welford's algorithm**, stored in Redis, updated only on traffic the existing 5 detectors judged clean:

- Redis key: `irochi:anomaly:baseline:{detector_domain}:{entity_type}:{entity_key}:{signal_name}` → hash with fields `count`, `mean`, `m2`. **No TTL** — this is long-lived state, not a window bucket (document as an `# OPEN` limitation that it never decays/resets — future work).
- For every numeric field in a `FeatureRecord.payload` (introspect via `payload.model_dump()`, skip `None`s):
  - If `count >= MIN_SAMPLES` (default 20): compute `z = (value - mean) / stddev` (guard `stddev == 0`).
  - Collect signals where `abs(z) >= Z_THRESHOLD` (default 3.0).
- **Decision logic** (needs the sibling detector's `Decision` for the *same* `FeatureRecord`, so this cannot be a normal registry-routed detector — see §3.4 for the integration point):
  - If the primary detector's decision was `NO_THREAT` and `>= MIN_DEVIATING_SIGNALS` (default 2) signals deviate → emit `DETECTION`, `threat_type = novel_anomaly`, `detector_id = anomaly_detector`, `confidence` = average deviating |z| capped to 1.0, `evidence.signals` in the **same shape** the other detectors already use (`signal_name`, `value`, `threshold`, `triggered`) plus `baseline_mean`/`baseline_stddev`/`z_score` per signal — this evidence shape is exactly what feature #6 ("baseline vs current behaviour") needed, so it comes for free; make sure `utils/explanation.ts`-style rendering on the frontend can show it as a baseline-vs-current box.
  - Update the Welford baseline **only when** the primary decision was `NO_THREAT` **and** this anomaly check itself did *not* fire — this prevents both known attacks and active novel anomalies from corrupting what "normal" means.
  - If `count < MIN_SAMPLES`, don't alert (return `INSUFFICIENT_DATA`) but still accumulate.

## 3. Backend — file-by-file plan

### 3.1 Enums (add in all 3 places, keep in sync — see §0)
- `schemas/detectors.py`: `DetectorId.ANOMALY = "anomaly_detector"`, `ThreatType.NOVEL_ANOMALY = "novel_anomaly"`.
- `schemas/alerts.py`: same two additions to its own separate `DetectorId`/`ThreatType` enums.
- `frontend/src/types/index.ts`: add `'anomaly_detector'` to `DetectorId`, `'novel_anomaly'` to `ThreatType`, plus entries in `DETECTOR_LABELS` ("Anomaly Detector") and `THREAT_TYPE_LABELS` ("Unknown / Novel Anomaly"). Do **not** add it anywhere the UI describes "the six threat classes" (e.g. `Capabilities.tsx` marketing copy) — it's explicitly a 7th, open-set catch-all, not one of the six. Grep the frontend for other hardcoded enumerations of exactly 5 detectors / 6 threat types (`DetectorHealth.tsx`, `ThreatBreakdown.tsx`, `Capabilities.tsx`, `Landing.tsx`) and decide per-instance whether the anomaly class belongs there, labeling it distinctly where it does.

### 3.2 `Incident` model + migration
New `backend/app/models/incident.py`, mirroring the style of `models/alert.py`:
```
incident_id            UUID, PK
entity_type            String
entity_key             String
status                 String   -- 'open' | 'closed'
opened_at              DateTime(tz)
updated_at             DateTime(tz)
last_event_at          DateTime(tz)
member_alert_ids       JSONB (list[str])
distinct_threat_types  JSONB (list[str])
risk_score             Float
risk_breakdown         JSONB (dict[str, float])
stage_state            String   -- 'anomaly'|'suspicious'|'likely_attack'|'confirmed_attack'
current_stage          String, nullable
forecast_next_stage    String, nullable
forecast_note          Text, nullable
schema_version         String
```
Add `CheckConstraint`s on `status` and `stage_state`, matching the style in `models/alert.py`. Also add a nullable `incident_id: Mapped[uuid.UUID | None]` column to `models/alert.py`.

New Alembic revision under `backend/alembic/versions/`, `down_revision = '85bbd9d419bc'`, following the exact style of `85bbd9d419bc_initial_schema.py`: `create_table('incidents', ...)` + `add_column('alerts', 'incident_id', UUID, nullable=True)`.

### 3.3 `IncidentEngine` + `PostgresIncidentService`
New `backend/app/services/postgres_incident_service.py`, mirroring `postgres_alert_service.py`: `create_incident`, `get_incident`, `get_open_incident_for_src_ip(src_ip, window_start)`, `update_incident_fields` (reuse the same optimistic-concurrency pattern via an `update_count`-less simple version is fine since incidents aren't concurrently written from multiple detectors at once — but check `alert_engine.py`'s stale-update handling and decide if it's needed here too), `list_incidents(status=None, limit=None)`.

New `backend/app/services/incident_engine.py` implementing the logic in §2.1–§2.4:
```python
class IncidentEngine:
    async def on_alert(self, alert_payload: dict, session: AsyncSession) -> None:
        # 1. find-or-open incident by src_ip within the 60-min window (§2.1)
        # 2. attach this alert_id to member_alert_ids, refresh last_event_at
        # 3. fetch all currently open member alerts for this incident from Postgres
        # 4. recompute risk_score / risk_breakdown (§2.2), stage_state / current_stage (§2.3),
        #    forecast_next_stage / forecast_note (§2.4)
        # 5. persist the incident, write incident_id back onto the Alert row
```
Wire this into `pipeline.py`'s `_process_message`: right after `await alert_engine.process_detector_output(output)` returns a non-`None` `alert_payload`, call `await incident_engine.on_alert(alert_payload, session)` using the same session. Instantiate `IncidentEngine` alongside `AlertEngine` in that same per-output session scope.

*(Optional, only if time remains: publish an incident-updated event on a separate Redis pub/sub channel, e.g. `irochi:incidents`, so the frontend can live-update the posture score / incident panel without polling — reuse `RedisPubSubService`.)*

### 3.4 Anomaly detector + baseline store
New `backend/app/services/detectors/baseline_state.py`: `BaselineStateStore` wrapping `RedisStateService` (add two small generic methods to `redis_client.py` if the existing `set_correlation`/`get_correlation` aren't a clean enough fit — name them for what they are, e.g. `get_state_hash`/`set_state_hash`, no TTL). Implements Welford `get_stats` / `update_stats` as in §2.5.

New `backend/app/services/detectors/anomaly.py`: `AnomalyDetector(BaseDetector)` with `detector_id = DetectorId.ANOMALY`. Because it needs the *sibling* detector's `Decision` for the same record (unlike every other detector, which is self-contained), **do not** wire it through the normal 1:1 `DOMAIN_TO_DETECTOR` path. Instead, in `DetectorRouter.route()`:
1. Run the existing primary-detector path exactly as today, producing `outputs`.
2. If an `AnomalyDetector` is registered (`registry.get_detector(DetectorId.ANOMALY)`), also call it directly on the same `detector_input` with the primary decision for context (extend its interface with e.g. `evaluate_against_baseline(self, inputs, primary_decision: Decision)` — keep the abstract `evaluate()` too, satisfied trivially, since `BaseDetector` requires it).
3. Append any anomaly `DetectorOutput`s (only non-empty ones) to the returned list.

Register it in `main.py` alongside the other 5 detectors, constructing it with a `BaselineStateStore(_state_service)`.

### 3.5 API
New `backend/app/schemas/incidents.py`: `IncidentResponse` (mirrors the model 1:1) + `IncidentListResponse`.
New `backend/app/api/routes/incidents.py`: `GET /incidents` (optional `?status=open`), `GET /incidents/{incident_id}` (404 if missing) — mirror `routes/alerts.py` exactly in structure and error handling.
Add `get_postgres_incident_service` to `dependencies.py`.
Register the router in `main.py`: `app.include_router(incident_routes.router, prefix=API_V1_PREFIX, tags=["incidents"])`.
Add `incident_id: str | None = None` to `AlertResponse` (`schemas/alerts.py`) and populate it in `from_orm`.

### 3.6 Tests
Follow the existing per-module test convention in `backend/tests/`. Add: `test_incident_engine.py` (fusion formula, stage ladder, forecast — table-driven, mirroring `test_recon_detector.py`'s style), `test_anomaly_detector.py` (baseline bootstrap → clean traffic below `MIN_SAMPLES` → `INSUFFICIENT_DATA`; established baseline + deviating sample + primary `NO_THREAT` → `DETECTION`; primary `DETECTION` → anomaly detector stays silent and doesn't update the baseline), `test_postgres_incident.py` (mirrors `test_postgres_alert.py`). Extend `test_pipeline.py` to assert an incident is created/updated after a `DetectorOutput` flows through.

## 4. Frontend — file-by-file plan

### 4.1 Types & API client
`types/index.ts`: enum additions from §3.1; add `incident_id?: string | null` to `Alert`; new `Incident` interface matching `IncidentResponse` 1:1.
`services/api.ts`: add `getIncident(incidentId)` and `listIncidents(status?)`, same `fetchJson` pattern as everything else.
New `hooks/useIncident.ts`, mirroring `hooks/useAlerts.ts` exactly (loading/error/isMock/refetch), taking an `incidentId: string | null` and returning `null` gracefully when there isn't one yet.

### 4.2 `IncidentPanel` (Risk Fusion + Early-Warning + Forecast)
New `components/IncidentPanel.tsx`:
- Risk score gauge/number (`risk_score`/100) + a breakdown table from `risk_breakdown` (per-threat-type contribution) — this is the doc's "Recon +15 / DGA +17 / … = 91" view.
- Stage ladder: render all 5 stages (`normal`→`anomaly`→`suspicious`→`likely_attack`→`confirmed_attack`), highlighting `stage_state`, same visual idiom as the existing "OBSERVED STAGES" chip row on `AlertDetailPage.tsx`.
- Forecast line: "Current stage: X · Potential next stage: Y" plus the fixed forecast disclaimer from §2.4, always visible, not just on hover.
- When `incident` is `null` (no backend incident yet), don't render this panel — fall back silently to the existing `progression.ts`-derived stage chips already on the page.

### 4.3 Replay / forensic timeline upgrade
On `AlertDetailPage.tsx`: call `useIncident(currentAlert.incident_id)`. If an incident is returned, drive the existing Play/Pause/Prev/Next controls off `incident.member_alert_ids` (fetch each member alert, order by timestamp) instead of `buildForensicTimeline`. At each step, render a new small `components/EvidenceChain.tsx` breadcrumb: **Raw Feature → Detector (`detector_id` @ `detector_version`) → Model (`model_version`, if present) → Score → Alert → Recommendation**, using fields that already exist on the alert (`source_feature_references`, `detector_version`, `model_version`, `score`) — no new backend data needed for this piece. If there's no `incident_id` (older alert / fallback), keep the current `correlation.ts`/`progression.ts` behavior exactly as-is.

### 4.4 Novel-anomaly presentation
Give `novel_anomaly` alerts a distinct badge/color (not one of the six existing threat-type colors) wherever severity/threat badges are rendered (`AlertTable.tsx`, `AlertDetailPage.tsx`, `RecentAlerts.tsx`, `LiveFeed.tsx`). When an alert's `evidence.signals` includes `baseline_mean`/`baseline_stddev` (only true for anomaly alerts, per §2.5), render a small "Baseline vs Current" comparison box instead of (or alongside) the normal signal table — this is a natural extension of the existing Explainable Evidence Panel on `AlertDetailPage.tsx`, not a new panel type.

### 4.5 Security Posture Score (do last, keep small)
On `Overview.tsx`, add a composite score at the top of the page: average `risk_score` across currently-open incidents (`listIncidents('open')`), or fall back to a severity-count-weighted calculation from the existing `DashboardSummaryResponse` if there are no open incidents yet. Show a small category breakdown (per `by_threat_type`) underneath, same visual language as the rest of the dashboard — do not invent a new design system for this.

## 5. Cleanup — resolve the Investigation.tsx duplication

`pages/Investigation.tsx` currently renders `MOCK_EVIDENCE_BY_ALERT` from `services/mockData.ts` behind an explicit "DEMO/MOCK DATA" banner, while `AlertDetailPage.tsx` is the real, fully-wired investigation view. This is confusing for a live demo. **Repurpose, don't just delete**: turn `Investigation.tsx` into a real **Incidents queue** — a table of open incidents from `GET /incidents`, sorted by `risk_score` descending, showing `stage_state`, `distinct_threat_types`, and member count, each row linking to `/app/alerts/{topAlertId}` (top alert = highest score in `member_alert_ids`) for full drill-down into `AlertDetailPage`. Remove the `MOCK_EVIDENCE_BY_ALERT` import and its only usage (confirmed nowhere else references it — safe to delete from `services/mockData.ts` too). Update the nav label in `layouts/AppLayout.tsx` (both entries, lines ~55 and ~73) from "Investigation" to "Incidents" to match. Keep the route path `/app/investigation` unless you'd rather rename it to `/app/incidents` — if you rename it, update `router.tsx` and both `AppLayout.tsx` nav entries together.

## 6. Acceptance criteria

- [ ] A synthetic sequence of alerts for one `src_ip` — recon → DGA → C2 → exfiltration — produces **one** incident whose `risk_score` reflects the escalation multiplier (visibly higher than the sum of any two alone) and whose `stage_state` reaches `confirmed_attack`.
- [ ] `forecast_next_stage` and the fixed disclaimer are present whenever `current_stage` has a defined next stage in `KILL_CHAIN_NEXT`, and `None`/absent when it doesn't (e.g. already at `data_exfiltration`).
- [ ] Feeding the anomaly detector < `MIN_SAMPLES` clean windows never alerts; feeding it a clear multi-signal deviation *after* baseline establishment, on traffic none of the 5 named detectors flagged, produces exactly one `novel_anomaly` `DETECTION` with `baseline_mean`/`baseline_stddev`/`z_score` per deviating signal in the evidence.
- [ ] Traffic that a named detector *does* flag never also triggers `novel_anomaly` for that same window, and never corrupts that entity's baseline.
- [ ] `AlertDetailPage.tsx` replay controls, when an `incident_id` is present, step through `member_alert_ids` and show a populated `EvidenceChain` at each step; when absent, behave exactly as they do today (no regression).
- [ ] The old `Investigation.tsx` mock banner is gone from the app; the nav item leads to a real, backend-fed incidents queue.
- [ ] All existing tests in `backend/tests/` still pass unmodified except where this brief explicitly says to extend them.

## 7. Explicitly out of scope for this pass

- Trained/ML anomaly models (Isolation Forest etc.) — statistical heuristic only, per the confirmed decision.
- Asset criticality, "what-if" simulation — not part of this brief.
- Baseline decay/reset policy — document as an `# OPEN` limitation, don't build it.
- Live Redis-pubsub push of incident updates — optional stretch item only, mentioned in §3.3, not required for acceptance.
