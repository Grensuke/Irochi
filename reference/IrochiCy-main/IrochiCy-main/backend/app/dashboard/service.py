"""Dashboard aggregation service with Redis caching."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
import structlog
from sqlalchemy import String, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.models import Alert
from app.dashboard.schemas import (
    DashboardSummary,
    KPIData,
    TimelineBucket,
    TimelineResponse,
    TopSourceIP,
    TopThreat,
)

logger = structlog.get_logger(__name__)

THREAT_TYPES = ["ddos", "recon", "dns_dga", "tls_c2", "exfiltration"]


async def get_kpi(db: AsyncSession, redis: aioredis.Redis) -> KPIData:
    """Build KPI data from DB queries and Redis pipeline metrics."""

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    current_hour = now.hour

    # Total alerts today
    today_result = await db.execute(
        select(func.count()).select_from(Alert).where(Alert.created_at >= today_start)
    )
    total_alerts_today = today_result.scalar_one()

    # Active threats (high/critical, not closed)
    active_result = await db.execute(
        select(func.count())
        .select_from(Alert)
        .where(
            Alert.severity.in_(["high", "critical"]),
            Alert.status != "closed",
        )
    )
    active_threats = active_result.scalar_one()

    # Pipeline metrics from Redis (set by the detection pipeline)
    events_per_second = float(await redis.get("pipeline:events_per_second") or 0)
    detectors_active = int(await redis.get("pipeline:detectors_active") or 0)
    pipeline_latency_p95_ms = int(await redis.get("pipeline:latency_p95_ms") or 0)

    # Delta: compare today's count to yesterday's same-hour window
    yesterday_same_window = await db.execute(
        select(func.count())
        .select_from(Alert)
        .where(
            Alert.created_at >= yesterday_start,
            Alert.created_at < yesterday_start + timedelta(hours=current_hour + 1),
        )
    )
    yesterday_count = yesterday_same_window.scalar_one()
    alerts_delta_today = total_alerts_today - yesterday_count

    return KPIData(
        total_alerts_today=total_alerts_today,
        active_threats=active_threats,
        events_per_second=events_per_second,
        detectors_active=detectors_active,
        pipeline_latency_p95_ms=pipeline_latency_p95_ms,
        alerts_delta_today=alerts_delta_today,
    )


async def get_timeline(db: AsyncSession) -> TimelineResponse:
    """Build 24 hourly buckets for the past 24 hours, broken down by threat type."""

    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=23)).replace(minute=0, second=0, microsecond=0)

    # Query hourly counts grouped by threat type
    rows = await db.execute(
        select(
            func.date_trunc("hour", Alert.created_at).label("bucket"),
            Alert.threat_type,
            func.count().label("cnt"),
        )
        .where(Alert.created_at >= start)
        .group_by("bucket", Alert.threat_type)
        .order_by("bucket")
    )

    # Index results for fast lookup
    data: dict[datetime, dict[str, int]] = {}
    for row in rows.all():
        bucket_dt = row[0]
        tt = row[1]
        cnt = row[2]
        if bucket_dt not in data:
            data[bucket_dt] = {}
        data[bucket_dt][tt] = cnt

    # Build 24 buckets, filling missing hours with zeros
    buckets: list[TimelineBucket] = []
    for i in range(24):
        bucket_time = start + timedelta(hours=i)
        counts = data.get(bucket_time, {})
        buckets.append(
            TimelineBucket(
                timestamp=bucket_time,
                ddos=counts.get("ddos", 0),
                recon=counts.get("recon", 0),
                dns_dga=counts.get("dns_dga", 0),
                tls_c2=counts.get("tls_c2", 0),
                exfiltration=counts.get("exfiltration", 0),
            )
        )

    return TimelineResponse(buckets=buckets)


async def get_top_threats(db: AsyncSession) -> list[TopThreat]:
    """Top threat types today with percentages."""

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    rows = await db.execute(
        select(Alert.threat_type, func.count().label("cnt"))
        .where(Alert.created_at >= today_start)
        .group_by(Alert.threat_type)
        .order_by(func.count().desc())
    )
    results = rows.all()
    total = sum(r[1] for r in results) or 1  # avoid div by zero

    return [
        TopThreat(
            threat_type=r[0],
            count=r[1],
            percentage=round(r[1] / total * 100, 1),
        )
        for r in results
    ]


async def get_top_source_ips(db: AsyncSession) -> list[TopSourceIP]:
    """Top 10 source IPs today with event counts and dominant threat type."""

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    rows = await db.execute(
        select(
            cast(Alert.src_ip, String).label("ip"),
            func.count().label("cnt"),
            func.max(Alert.created_at).label("last_seen"),
            func.mode().within_group(Alert.threat_type).label("top_threat"),
        )
        .where(Alert.created_at >= today_start)
        .group_by(Alert.src_ip)
        .order_by(func.count().desc())
        .limit(10)
    )

    return [
        TopSourceIP(
            ip=r[0],
            event_count=r[1],
            alert_count=r[1],
            last_seen=r[2],
            top_threat=r[3],
        )
        for r in rows.all()
    ]


async def get_dashboard_summary(
    db: AsyncSession, redis: aioredis.Redis
) -> DashboardSummary:
    """
    Full dashboard summary with 5-second Redis cache.
    """
    cache_key = "cache:dashboard:summary"

    # Try cache first
    try:
        cached = await redis.get(cache_key)
        if cached:
            return DashboardSummary.model_validate_json(cached)
    except Exception as exc:
        logger.warning("dashboard_cache_read_failed", error=str(exc))

    # Build fresh
    kpi = await get_kpi(db, redis)
    top_threats = await get_top_threats(db)
    top_source_ips = await get_top_source_ips(db)

    summary = DashboardSummary(
        kpi=kpi,
        top_threats=top_threats,
        top_source_ips=top_source_ips,
    )

    # Cache for 5 seconds
    try:
        await redis.set(cache_key, summary.model_dump_json(), ex=5)
    except Exception as exc:
        logger.warning("dashboard_cache_write_failed", error=str(exc))

    return summary
