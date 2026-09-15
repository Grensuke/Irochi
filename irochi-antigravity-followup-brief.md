# Irochi — Fix-Up & Verification Pass + Attack Replay (Full Spec)

## 0. Context

This is a follow-up to a previous pass that implemented: correlation by src_ip within a 60-minute window, a weighted incident risk score with kill-chain escalation, a Welford-based unknown-threat anomaly detector wired into `DetectionPipeline`, an Incident Queue replacing the old mock Investigation page, and an `IncidentPanel` + `EvidenceChain` on `AlertDetailPage`. That pass reported success, but its summary was vague enough that several specific pieces are unconfirmed — and one, Attack Replay, looks like it shipped as a static diagram rather than the interactive feature that was actually asked for.

This pass has two jobs, **in order**:

1. **Audit and fix** the items in §1. Each has a specific, checkable test — don't eyeball the code and assume it's fine; add and run the described test, and only mark an item done once it actually passes.
2. **Build Attack Replay properly** — §2 is the full spec. Treat this as the primary deliverable of this pass; the previous attempt appears to have only added a static `EvidenceChain` component next to `IncidentPanel`, not the interactive stepping behavior that was requested.

Report back using the exact format in §3 — one line per item, not a narrative summary. A paragraph like "AlertDetailPage displays an IncidentPanel alongside an EvidenceChain" is not an acceptable report for this pass; say explicitly, per item, what was found and how it was verified.

## 1. Audit & fix checklist

Go through each item in order. For each: locate the relevant existing code, determine whether it actually does what's described, fix if not, and note the verification method used.

### 1.1 Security Posture Score (`Overview.tsx`)
- Check: does `frontend/src/pages/Overview.tsx` render a composite score derived from open incidents' `risk_score` (averaged across `listIncidents('open')`), with a fallback to a severity-count-weighted calculation from `DashboardSummaryResponse` when there are no open incidents?
- If missing: implement it now, reusing the existing `SummaryBar` card style — don't introduce a new visual pattern. Include a small per-category breakdown underneath, from `by_threat_type`.

### 1.2 Forecast disclaimer
- Check: wherever `forecast_next_stage` is rendered (should be in `IncidentPanel.tsx`), is the fixed line — *"This is a risk forecast based on observed kill-chain progression, not a claim that the next stage has occurred."* — always visible alongside it, not tucked into a tooltip or conditionally hidden?
- Fix if it's missing, or only shown some of the time.

### 1.3 Baseline-corruption guard (highest-risk item — check this carefully)
- In `services/detectors/anomaly.py` / `baseline_state.py`, confirm `update_stats` runs **only** when: the primary detector's decision for that window was `NO_THREAT`, **and** the anomaly check itself did not fire that window.
- Add if missing: `test_anomaly_detector.py::test_baseline_not_updated_during_known_attack` and `::test_baseline_not_updated_during_active_anomaly` — feed a window where the primary decision is `DETECTION` through the anomaly path and assert the Redis baseline hash for that entity/signal is byte-for-byte unchanged before vs after. Run both. Fix the guard condition in `anomaly.py` if either fails, then re-run.

### 1.4 Escalation math
- Add if missing: `test_incident_engine.py::test_escalation_multiplier_applied` — construct an incident with exactly 3 distinct threat types at known confidences, hand-compute the expected `risk_score` from the formula (`raw_score * (1 + 0.15*(distinct_types-1))`, capped at 100), assert the engine matches, and separately assert the result is strictly greater than a plain `sum(contribution.values())` would give.
- Fix `incident_engine.py` if it's summing without the multiplier.

### 1.5 DDoS stage handling
- Confirm `incident_engine.py` special-cases `volumetric_ddos` (severity-based → `likely_attack` if high/critical else `suspicious`) instead of feeding it through the linear `KILL_CHAIN_ORDER`.
- Add `test_incident_engine.py::test_ddos_does_not_enter_linear_kill_chain` if missing. Fix if DDoS is being treated as a kill-chain stage.

### 1.6 Fallback path for alerts with no incident
- Manually open an alert with `incident_id = None` on `AlertDetailPage.tsx`. Confirm it still renders via the original `correlation.ts`/`progression.ts` path, with no console errors and nothing rendering blank/broken.
- Fix any place that now hard-assumes `incident_id` is non-null.

### 1.7 Enum sync
- Run: `grep -rn "novel_anomaly\|anomaly_detector" backend/app/schemas/ frontend/src/types/index.ts`
- Confirm both values exist, with matching strings, in all three locations (`schemas/detectors.py`, `schemas/alerts.py`, `frontend/src/types/index.ts`) and that `DETECTOR_LABELS`/`THREAT_TYPE_LABELS` have entries for them. Fix any gap found.

### 1.8 Tests exist and pass
- Confirm `test_incident_engine.py`, `test_anomaly_detector.py`, `test_postgres_incident.py` exist (add any missing). Run the full `pytest` suite and report the actual pass/fail count — not just "tests were added."

## 2. Attack Replay — build this properly

### 2.1 Data flow
On `AlertDetailPage.tsx`, when `currentAlert.incident_id` is present:
1. Fetch the incident via `useIncident(currentAlert.incident_id)`.
2. Fetch every alert in `incident.member_alert_ids` (per-alert `getAlert(id)` calls are fine given the small member counts — no need for a new batch endpoint unless one already fits naturally).
3. Sort the fetched member alerts by timestamp ascending — this ordered list **is** the replay sequence, replacing whatever `buildForensicTimeline` produced when an incident exists.

### 2.2 Replay controls must be genuinely interactive
Keep the existing Play/Pause/Prev/Next UI, but rewire it against the ordered member-alert list:
- `currentStepIndex` state, 0-indexed.
- **Play** advances the index every 2.5s, stopping automatically at the last step.
- **Pause** stops the interval and holds the current step.
- **Next/Prev** move the index by exactly ±1, clamped to bounds, and stop any running interval.
- The step indicator ("Step 3 of 6") must visibly update on every interaction — confirm by clicking Next repeatedly.

### 2.3 What must change per step (this is the part most likely to have been faked as static last time)
At each `currentStepIndex`:
- Re-render `EvidenceChain` for **that specific step's alert** (`memberAlerts[currentStepIndex]`) — not a single fixed chain for the whole incident, and not derived from `currentAlert` (the alert the page was originally opened on) or from `incident` as a whole. Explicitly check the props passed into `EvidenceChain` actually change as `currentStepIndex` changes.
- Re-render the per-alert evidence/signal table (`utils/explanation.ts` output) for that step's alert.
- Optional, only if time allows: grow the `NarrativePanel` narrative to reflect only alerts observed up to and including the current step, rather than always the full-incident narrative. Not required for acceptance.

### 2.4 Fallback
If `currentAlert.incident_id` is `None`, replay must behave exactly as before this work started — stepping through the `correlation.ts`-derived client-side timeline. Do not remove that path.

### 2.5 Acceptance criteria for Attack Replay specifically
- [ ] Opening an alert in a ≥3-member incident and clicking Play visibly auto-advances through steps and stops at the end.
- [ ] Next/Prev move exactly one step per click, in the right direction, while paused.
- [ ] `EvidenceChain` content (detector name, model version, score) visibly differs between at least two steps in a multi-detector incident — if it's identical across every step, the wiring is wrong and needs fixing.
- [ ] An alert with no `incident_id` still replays via the original path, no errors.
- [ ] If the frontend already has a component/interaction test convention (check for `__tests__`/`*.test.tsx` before deciding), add coverage for the stepping behavior; don't introduce a new test framework if none exists.

## 3. Required reporting format

Report every item from §1 and §2 as one line each, in this exact form — not prose paragraphs:

```
[FIXED | ALREADY OK | NEW] <item> — verified via: <specific check performed>
```

Example: `[FIXED] Baseline-corruption guard — was updating baseline even when primary detector fired; added test_baseline_not_updated_during_known_attack, now passes.`

If an item in §1 was already correct, still state what verification was performed — "looks fine" on its own is not acceptable for this pass.
