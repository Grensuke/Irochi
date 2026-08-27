# Integration Notes — Irochi

> **This file tracks active frontend ↔ backend integration requests.**
> It is for current integration work, not permanent architecture history.
> Resolved items can be moved to a "Resolved" section or archived.

---

## Format

```
INT-###
Title:
From:        (requesting area: frontend / backend)
To:          (target area: backend / frontend)
Status:      (open / in-progress / resolved / blocked)
Requirement:
Notes:
```

---

## Active Items

### INT-001

**Title:** Dummy alert list endpoint
**From:** Frontend
**To:** Backend
**Status:** Open
**Requirement:** Frontend needs a `GET /api/v1/alerts` endpoint returning mock alerts with the fields specified in `API_CONTRACT.md`. Each alert must include `threat_type` (one of six capabilities) and `detector_id` (one of five modules).
**Notes:** Blocked until Checkpoint 2 (backend skeleton). Frontend will use local mock data until this endpoint exists.

### INT-002

**Title:** Dummy WebSocket for live alerts
**From:** Frontend
**To:** Backend
**Status:** Open
**Requirement:** Frontend needs a `WS /api/v1/ws/alerts` endpoint that simulates backfill + live alert delivery. Messages should distinguish between "backfill" and "live" phases.
**Notes:** Blocked until Checkpoint 2 (backend skeleton). See `API_CONTRACT.md` for preliminary message structure.

---

## Resolved Items

_(none yet)_
