# Data Contracts — Irochi

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

### Five Detector Modules

| ID | Module |
|---|---|
| `ddos_detector` | DDoS Detector |
| `recon_detector` | Recon Detector |
| `dns_dga_tunnel_detector` | DNS/DGA/DNS-Tunneling Detector |
| `tls_c2_detector` | TLS/C2 Detector |
| `exfiltration_detector` | Exfiltration Detector |

### Six Threat Capabilities

| ID | Capability |
|---|---|
| `volumetric_ddos` | Volumetric / Protocol DDoS |
| `c2_beaconing` | Botnet C2 Beaconing |
| `dga_dns_tunnel` | DGA / DNS Tunneling |
| `encrypted_malware` | Malware inside encrypted sessions |
| `recon_portscan` | Reconnaissance / Port Scanning |
| `data_exfiltration` | Data Exfiltration |

One detector module may emit multiple threat classes. These are **not** six microservices.

---

## Contracts Not Yet Defined

The following data contracts are part of the design chain and will be defined in sequence:

1. ~~Canonical Event Schema~~ — **complete** (baseline)
2. Redpanda Topics — pending
3. Feature / Window Schema — pending
4. Detector Inputs / Outputs — pending
5. Alert Schema — pending
6. PostgreSQL Schema — pending
