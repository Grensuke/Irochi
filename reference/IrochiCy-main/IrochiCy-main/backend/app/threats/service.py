"""Threat intelligence service with static definitions and live DB queries."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import redis.asyncio as aioredis
import structlog
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.models import Alert
from app.alerts.schemas import AlertResponse
from app.threats.schemas import (
    ConfidenceBucket,
    SignalDefinition,
    ThreatDetailResponse,
    ThreatTypeStat,
)

logger = structlog.get_logger(__name__)

# ── Static threat definitions ────────────────────────────────────

THREAT_DEFINITIONS: dict[str, dict[str, Any]] = {
    "ddos": {
        "display_name": "DDoS Attack",
        "description": (
            "Monitors connection telemetry for volumetric attack patterns. "
            "Derives packet_rate, byte_rate, syn_ratio, and source_ip_entropy over "
            "rolling windows. Triggers on rate thresholds and entropy spikes indicating "
            "distributed source traffic."
        ),
        "signals": [
            {"name": "packet_rate", "signal_type": "derived", "description": "Packets per second from source", "threshold": ">10000 pkt/s", "weight": 0.35},
            {"name": "syn_ratio", "signal_type": "derived", "description": "Ratio of SYN to total packets", "threshold": ">0.85", "weight": 0.30},
            {"name": "source_ip_entropy", "signal_type": "derived", "description": "Shannon entropy of unique source IPs", "threshold": ">7.0 bits", "weight": 0.20},
            {"name": "byte_rate", "signal_type": "derived", "description": "Bytes per second throughput", "threshold": ">100 MB/s", "weight": 0.15},
        ],
    },
    "recon": {
        "display_name": "Reconnaissance / Port Scan",
        "description": (
            "Tracks port scanning and host discovery behavior by windowing "
            "unique destination ports and hosts per source IP. Detects horizontal and "
            "vertical scans using statistical thresholds on connection_fan_out and scan_rate."
        ),
        "signals": [
            {"name": "unique_dst_ports", "signal_type": "derived", "description": "Distinct destination ports in window", "threshold": ">1000 in 60s", "weight": 0.40},
            {"name": "unique_dst_hosts", "signal_type": "derived", "description": "Distinct destination hosts in window", "threshold": ">500 in 60s", "weight": 0.30},
            {"name": "connection_fan_out", "signal_type": "derived", "description": "One-to-many connection ratio", "threshold": "HIGH", "weight": 0.20},
            {"name": "scan_rate", "signal_type": "derived", "description": "New connection attempts per second", "threshold": ">50 conn/s", "weight": 0.10},
        ],
    },
    "dns_dga": {
        "display_name": "DNS / DGA / DNS Tunneling",
        "description": (
            "Analyzes DNS query telemetry from Zeek dns.log for algorithmically "
            "generated domain names and DNS tunneling. Scores by domain_entropy, n-gram "
            "likelihood, label-length statistics, and query_frequency. XGBoost classifier "
            "trained on labeled DGA corpora."
        ),
        "signals": [
            {"name": "domain_entropy", "signal_type": "derived", "description": "Shannon entropy of queried domain", "threshold": ">3.8 bits", "weight": 0.30},
            {"name": "n_gram_score", "signal_type": "derived", "description": "N-gram language model likelihood score", "threshold": "<0.15", "weight": 0.35},
            {"name": "query_length", "signal_type": "derived", "description": "Total character length of FQDN", "threshold": ">45 chars", "weight": 0.15},
            {"name": "query_frequency", "signal_type": "derived", "description": "Query rate per client per minute", "threshold": ">100/min", "weight": 0.20},
        ],
    },
    "tls_c2": {
        "display_name": "TLS Fingerprint / C2 Beacon",
        "description": (
            "Inspects TLS session fingerprints (JA3 from Zeek ssl.log) against "
            "Abuse.ch SSLBL blacklist. Separately monitors inter-arrival timing for beacon "
            "periodicity. JA3 hit alone = medium confidence; combined with timing regularity "
            "= high confidence C2 classification."
        ),
        "signals": [
            {"name": "ja3_blacklist_match", "signal_type": "intel", "description": "JA3 fingerprint match in SSLBL", "threshold": "HIT", "weight": 0.50},
            {"name": "beacon_periodicity", "signal_type": "derived", "description": "Regularity score of inter-arrival times", "threshold": "regularity > 0.90", "weight": 0.30},
            {"name": "inter_arrival_time", "signal_type": "derived", "description": "Std dev of connection spacing over 30min", "threshold": "std_dev < 2s", "weight": 0.20},
        ],
    },
    "exfiltration": {
        "display_name": "Data Exfiltration",
        "description": (
            "Detects sustained large outbound data transfers by windowing "
            "outbound_inbound_ratio and rolling transfer volume. Flags sessions with "
            "byte asymmetry exceeding thresholds over configurable time windows."
        ),
        "signals": [
            {"name": "outbound_inbound_ratio", "signal_type": "derived", "description": "Ratio of outbound to inbound bytes", "threshold": ">10.0", "weight": 0.40},
            {"name": "rolling_transfer_bytes", "signal_type": "derived", "description": "Rolling outbound bytes in window", "threshold": ">500MB in 15min", "weight": 0.40},
            {"name": "byte_rate", "signal_type": "derived", "description": "Sustained outbound byte rate", "threshold": ">50 MB/s", "weight": 0.20},
        ],
    },
}


async def _get_threat_stat(
    db: AsyncSession,
    redis: aioredis.Redis,
    threat_type: str,
) -> ThreatTypeStat:
    """Build a ThreatTypeStat for one threat type by merging static + live data."""

    defn = THREAT_DEFINITIONS[threat_type]
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    # Run all 4 queries concurrently
    today_q = db.execute(
        select(func.count()).select_from(Alert).where(
            Alert.threat_type == threat_type,
            Alert.created_at >= today_start,
        )
    )
    week_q = db.execute(
        select(func.count()).select_from(Alert).where(
            Alert.threat_type == threat_type,
            Alert.created_at >= week_ago,
        )
    )
    avg_q = db.execute(
        select(func.avg(Alert.confidence)).where(
            Alert.threat_type == threat_type,
            Alert.created_at >= today_start,
        )
    )
    last_q = db.execute(
        select(func.max(Alert.created_at)).where(Alert.threat_type == threat_type)
    )

    today_r, week_r, avg_r, last_r = await asyncio.gather(
        today_q, week_q, avg_q, last_q
    )

    alerts_today = today_r.scalar_one()
    alerts_7d = week_r.scalar_one()
    avg_confidence = round(float(avg_r.scalar_one() or 0), 4)
    last_detection = last_r.scalar_one()

    # Detector status from Redis
    try:
        det_status = await redis.get(f"pipeline:detector:{threat_type}:status")
        detector_status = det_status if det_status in ("running", "idle", "error") else "idle"
    except Exception:
        detector_status = "idle"

    return ThreatTypeStat(
        threat_type=threat_type,
        display_name=defn["display_name"],
        description=defn["description"],
        signals=[SignalDefinition(**s) for s in defn["signals"]],
        alerts_today=alerts_today,
        alerts_7d=alerts_7d,
        avg_confidence=avg_confidence,
        detector_status=detector_status,
        last_detection=last_detection,
    )


async def get_threat_types(
    db: AsyncSession,
    redis: aioredis.Redis,
) -> list[ThreatTypeStat]:
    """Get stats for all 5 threat types concurrently."""
    tasks = [
        _get_threat_stat(db, redis, tt)
        for tt in THREAT_DEFINITIONS
    ]
    return list(await asyncio.gather(*tasks))


async def get_threat_detail(
    db: AsyncSession,
    redis: aioredis.Redis,
    threat_type: str,
) -> ThreatDetailResponse:
    """Get detailed view for a single threat type with confidence distribution."""

    if threat_type not in THREAT_DEFINITIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown threat type: '{threat_type}'. "
                   f"Valid types: {list(THREAT_DEFINITIONS.keys())}",
        )

    # Get the stat
    stat = await _get_threat_stat(db, redis, threat_type)

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Confidence distribution (10 buckets: 0-10%, 10-20%, ..., 90-100%)
    dist_rows = await db.execute(
        select(
            (func.floor(Alert.confidence * 10) * 10).label("bucket_start"),
            func.count().label("cnt"),
        )
        .where(
            Alert.threat_type == threat_type,
            Alert.created_at >= today_start,
        )
        .group_by("bucket_start")
        .order_by("bucket_start")
    )

    # Build all 10 buckets, filling missing with zero
    dist_data = {int(r[0]): r[1] for r in dist_rows.all()}
    confidence_distribution = []
    for i in range(10):
        start = i * 10
        end = (i + 1) * 10
        label = f"{start}–{end}%"
        confidence_distribution.append(
            ConfidenceBucket(
                bucket_label=label,
                count=dist_data.get(start, 0),
            )
        )

    # Recent 10 alerts for this threat type
    recent_result = await db.execute(
        select(Alert)
        .where(Alert.threat_type == threat_type)
        .order_by(Alert.created_at.desc())
        .limit(10)
    )
    recent_alerts = [
        AlertResponse.model_validate(a) for a in recent_result.scalars().all()
    ]

    return ThreatDetailResponse(
        threat_type=threat_type,
        stat=stat,
        confidence_distribution=confidence_distribution,
        recent_alerts=recent_alerts,
    )
