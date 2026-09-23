# Data Contracts — Vibhinetra

> **This file documents cross-team data contracts.**
> It references the canonical sources rather than duplicating them.

---

## Canonical Event Schema

**Source of truth:**

[`docs/data/CANONICAL_EVENT_SCHEMA_FINAL.md`](../data/CANONICAL_EVENT_SCHEMA_FINAL.md)

The Canonical Event Schema defines the source-independent event contract produced by the Python Ingest Normalizer before events enter Redpanda. It uses an envelope + typed payload structure:

```
CanonicalEvent
├── Envelope (common fields: event_id, event_type, connection_id, timestamp, ...)
└── Typed Payload
    ├── ConnectionPayload (Zeek conn.log, NetFlow, IPFIX)
    ├── DnsPayload (Zeek dns.log)
    └── TlsPayload (Zeek ssl.log + JA3/JA4 packages)
```

**Do not create a contradictory duplicate schema.** Always refer to the canonical document above.

---

## Raw vs Derived Boundary

This separation is **locked**:

| Layer | Contains | Examples |
|---|---|---|
| Canonical Event | Observed / normalized facts | `src_ip`, `dst_ip`, `orig_bytes`, `ja3`, `query` |
| Feature / Window Schema | Calculated / derived values | `packet_rate`, `domain_entropy`, `ja3_blacklist_match` |
| Detector Result | Interpretation / classification | `threat_type`, `confidence`, `evidence` |
| Alert | Analyst-facing security record | `alert_id`, `severity`, `status` |

---

## Threat Taxonomy

### Six Detector Modules

| ID | Module |
|---|---|
| `ddos_detector` | DDoS Detector |
| `recon_detector` | Recon Detector |
| `dns_dga_tunnel_detector` | DNS/DGA/DNS-Tunneling Detector |
| `tls_c2_detector` | TLS/C2 Detector |
| `exfiltration_detector` | Exfiltration Detector |
| `unknown_detector` | Unknown Detector |

### Seven Threat Capabilities

| ID | Capability |
|---|---|
| `volumetric_ddos` | Volumetric / Protocol DDoS |
| `c2_beaconing` | Botnet C2 Beaconing |
| `dga_dns_tunnel` | DGA / DNS Tunneling |
| `encrypted_malware` | Malware inside encrypted sessions |
| `recon_portscan` | Reconnaissance / Port Scanning |
| `data_exfiltration` | Data Exfiltration |
| `unknown_threat` | Unknown threat / baseline deviation |

One detector module may emit multiple threat classes. These are **not** seven microservices.

---

## Downstream Contracts

The following data contracts were defined in sequence and are now actively implemented in the current pipeline (PostgreSQL, Redpanda, Redis, FastAPI). While some underlying specification documents retain their "DRAFT" moniker, the contracts they define are live in the codebase:

1. Canonical Event Schema — **Active**
2. Redpanda Topics — **Active** (raw partition key locked)
3. Feature / Window Schema — **Active**
4. Detector Inputs / Outputs — **Active**
5. Alert Schema — **Active** (durable persistence)
6. PostgreSQL Schema — **Active**
7. Final API Contract — **Active** (FastAPI / WebSocket)
