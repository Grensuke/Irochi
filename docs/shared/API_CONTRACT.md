# API Contract — Irochi

> **⚠️ DRAFT / TEMPORARY DUMMY CONTRACT**
>
> These endpoints are temporary dummy endpoints.
> They are **NOT** the final API contract.
> The final API contract will be defined after the architecture design chain
> (Redpanda Topics → Feature/Window Schema → Detector Contracts → Alert Schema → PostgreSQL Schema → API Contract)
> is completed.

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
2. Server sends a simulated backfill batch (existing mock alerts)
3. Server enters live mode
4. Server periodically sends new mock alerts
5. Messages distinguish between "backfill" and "live" phases

**Message structure (preliminary):**

```json
{
  "type": "backfill | live",
  "alert": { "...alert object" }
}
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
