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
2. Redpanda Topics — **DRAFT / IN PROGRESS**
   - raw partition key = **LOCKED**
   - remaining transport/topic decisions = **OPEN**
3. Feature / Window Schema — **DRAFT / IN PROGRESS**
   - window-type taxonomy = **LOCKED**
   - feature-level mapping = **PROPOSED**
   - remaining state/parameter decisions = **OPEN**
4. Detector Inputs / Outputs — **DRAFT / IN PROGRESS**
   - detector taxonomy (5 IDs, 6 threat types) = **inherited** (BD-008 Active)
   - DetectorInput envelope = **PROPOSED**
   - typed payload strategy (Option C) = **PROPOSED**
   - base grouping identity = **PROPOSED**
   - per-detector input contracts = **PROPOSED**
   - partial-input policy = **PROPOSED**
   - DetectorOutput envelope = **PROPOSED**
   - decision enum = **PROPOSED**
   - threat-type mapping = **PROPOSED**
   - temporal association policy = **OPEN**
   - confidence/score semantics = **OPEN**
   - evidence structure details = **OPEN**
   - evaluation trigger model = **OPEN**
5. Alert Schema — **DRAFT / IN PROGRESS**
   - detector/threat taxonomy = **inherited** (BD-008 Active)
   - alert envelope = **PROPOSED**
   - DetectorOutput → Alert mapping = **PROPOSED**
   - lifecycle status enum = **PROPOSED**
   - dedup identity structure = **PROPOSED**
   - evidence/provenance model = **PROPOSED**
   - severity ownership = **PROPOSED**
   - PostgreSQL/Redis boundaries = **PROPOSED**
   - temporal dedup scoping = **OPEN**
   - exact dedup algorithm = **OPEN**
   - cross-detector correlation = **OPEN**
   - confidence/score semantics = **OPEN**
   - evidence field typing = **OPEN**
6. PostgreSQL Schema — **DRAFT / IN PROGRESS**
   - durable alert persistence model = **PROPOSED**
   - logical relational/JSON representation = **PROPOSED**
   - indexing/retention/partitioning/implementation details = **OPEN**
