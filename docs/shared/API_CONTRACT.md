# API Contract — Irochi (Historical / Temporary Dummy)

> **⚠️ HISTORICAL / TEMPORARY DUMMY CONTRACT — preserved for reference**
>
> This file is the original **temporary dummy** API contract created during Checkpoint 2.
> It is preserved as a historical record of the dummy phase.
>
> **The current API Contract draft is:**
> [`docs/shared/API_CONTRACT_DRAFT_v1.md`](./API_CONTRACT_DRAFT_v1.md)
>
> That document is still **DRAFT** and is **not yet FINAL**. It contains PROPOSED and OPEN items.
>
> This file is **NOT** deleted or overwritten.
> Do not use this file as the design source of truth for implementation.
> Use `API_CONTRACT_DRAFT_v1.md` for current design reference.

---

> **Original header (preserved):**
>
> These endpoints are temporary dummy endpoints.
> They are **NOT** the final API contract.
> The design chain (Redpanda Topics → Feature/Window Schema → Detector Contracts → Alert Schema → PostgreSQL Schema → API Contract)
> has been completed up to the Draft stage. See `API_CONTRACT_DRAFT_v1.md` for the current contract draft.

---

## Base Path

```
/api/v1
```

---

## Endpoints

### GET /api/v1/health

Health check endpoint.

**Response:** `200 OK`

```json
{
  "status": "ok"
}
```

---

### GET /api/v1/alerts

List mock alerts.

**Response:** `200 OK`

```json
{
  "alerts": [
    {
      "alert_id": "string",
      "timestamp": "string (ISO 8601)",
      "threat_type": "string",
      "detector_id": "string",
      "severity": "string",
      "confidence": "number (0.0–1.0)",
      "src_ip": "string",
      "dst_ip": "string",
      "evidence_summary": "string",
      "status": "string"
    }
  ],
  "total": "integer"
}
```

---

### GET /api/v1/alerts/{alert_id}

Get a single alert by ID.

**Response:** `200 OK` — alert object (same structure as above)

**Response:** `404 Not Found` — alert not found

```json
{
  "detail": "Alert not found"
}
```

---

### GET /api/v1/dashboard/summary

Dashboard summary metrics.

**Response:** `200 OK`

```json
{
  "total_alerts": "integer",
  "critical_count": "integer",
  "high_count": "integer",
  "medium_count": "integer",
  "low_count": "integer",
  "info_count": "integer",
  "by_threat_type": {
    "threat_type_name": "integer"
  },
  "by_detector": {
    "detector_id": "integer"
  },
  "recent_alerts": ["...abbreviated alert objects"]
}
```

---

### WS /api/v1/ws/alerts

WebSocket endpoint for live alert delivery.

**Dummy behaviour:**

1. Client connects
2. Server sends backfill alerts (existing mock alerts)
3. Server sends a `backfill_complete` transition marker
4. Server enters live mode
5. Server periodically sends new mock alerts

**Message types:**

#### `backfill`

Sent during the backfill phase. Contains a historical alert.

```json
{
  "type": "backfill",
  "alert": { "...alert object" }
}
```

#### `backfill_complete`

Transition marker sent once after all backfill alerts. Contains `alert: null`.

```json
{
  "type": "backfill_complete",
  "alert": null
}
```

#### `live`

Sent during the live phase. Contains a newly generated alert.

```json
{
  "type": "live",
  "alert": { "...alert object" }
}
```

**Expected sequence:**

```text
backfill × N
    ↓
backfill_complete
    ↓
live × N
```

> **Note:** This WebSocket protocol is a dummy simulation.
> PostgreSQL and Redis Pub/Sub are NOT implemented yet.
> The real WebSocket protocol will be defined as part of the final API contract.

---

## Threat Type Values

| Value | Description |
|---|---|
| `volumetric_ddos` | Volumetric / Protocol DDoS |
| `c2_beaconing` | Botnet C2 Beaconing |
| `dga_dns_tunnel` | DGA / DNS Tunneling |
| `encrypted_malware` | Malware inside encrypted sessions |
| `recon_portscan` | Reconnaissance / Port Scanning |
| `data_exfiltration` | Data Exfiltration |

## Detector ID Values

| Value | Description |
|---|---|
| `ddos_detector` | DDoS Detector |
| `recon_detector` | Recon Detector |
| `dns_dga_tunnel_detector` | DNS/DGA/DNS-Tunneling Detector |
| `tls_c2_detector` | TLS/C2 Detector |
| `exfiltration_detector` | Exfiltration Detector |

## Severity Values

```
critical | high | medium | low | info
```

## Alert Status Values

```
new | investigating | closed | false_positive
```

> "Closed" is an analyst workflow status. It does NOT imply that Irochi mitigated or stopped the threat.
