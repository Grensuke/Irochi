"""
Alert engine: consumes detector results from Redpanda, deduplicates,
assigns severity, persists to PostgreSQL, and publishes to Redis Pub/Sub.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import redis.asyncio as aioredis
import structlog
from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.alert_engine.schemas import DetectorResult
from app.alerts.models import Alert
from app.alerts.schemas import AlertResponse
from app.config import settings

logger = structlog.get_logger(__name__)

TOPIC = "detector.results"

# ── Severity thresholds ──────────────────────────────────────────

SEVERITY_THRESHOLDS = {
    "critical": 0.90,
    "high": 0.70,
    "medium": 0.45,
    "low": 0.00,
}


def assign_severity(confidence: float) -> str:
    """Return the highest severity bracket that the confidence meets or exceeds."""
    for severity, threshold in SEVERITY_THRESHOLDS.items():
        if confidence >= threshold:
            return severity
    return "low"


# ── Deduplication ────────────────────────────────────────────────

async def is_duplicate(redis: aioredis.Redis, result: DetectorResult) -> bool:
    """
    Check if this alert is a duplicate within a 2-minute window.
    Key: dedup:{threat_type}:{src_ip}:{dst_ip}
    """
    key = f"dedup:{result.threat_type}:{result.src_ip}:{result.dst_ip}"
    exists = await redis.exists(key)
    if exists:
        return True
    await redis.set(key, 1, ex=120)  # 2-minute dedup window
    return False


# ── Core processing ──────────────────────────────────────────────

async def process_detector_result(
    db: AsyncSession,
    redis: aioredis.Redis,
    result: DetectorResult,
) -> None:
    """
    Process a single detector result:
    1. Deduplicate
    2. Assign severity
    3. Persist to DB
    4. Calculate ingest latency
    5. Publish to Redis for WebSocket broadcast
    """

    # 1. Deduplication
    if await is_duplicate(redis, result):
        logger.debug(
            "alert_deduplicated",
            threat_type=result.threat_type,
            src_ip=result.src_ip,
            dst_ip=result.dst_ip,
        )
        return

    # 2. Assign severity
    severity = assign_severity(result.confidence)

    # 3. Persist to database
    new_alert = Alert(
        threat_type=result.threat_type,
        severity=severity,
        confidence=result.confidence,
        src_ip=result.src_ip,
        dst_ip=result.dst_ip,
        src_port=result.src_port,
        dst_port=result.dst_port,
        protocol=result.protocol,
        detector_id=result.detector_id,
        schema_version=result.schema_version,
        sensor_source=result.sensor_source,
        evidence=[e.model_dump() for e in result.evidence],
        raw_event_id=result.event_id,
    )
    db.add(new_alert)

    try:
        await db.commit()
        await db.refresh(new_alert)
    except Exception as exc:
        await db.rollback()
        logger.error("alert_commit_failed", error=str(exc))
        return  # DO NOT publish to Redis if commit failed

    # 4. Calculate and store ingest latency
    latency_ms = int(
        (datetime.utcnow() - result.detected_at).total_seconds() * 1000
    )
    try:
        await db.execute(
            update(Alert)
            .where(Alert.id == new_alert.id)
            .values(ingest_latency_ms=latency_ms)
        )
        await db.commit()
    except Exception as exc:
        logger.warning("latency_update_failed", error=str(exc))

    # 5. Publish to Redis for real-time WebSocket broadcast
    try:
        alert_payload = AlertResponse.model_validate(new_alert).model_dump_json()
        await redis.publish("alerts:live", alert_payload)
    except Exception as exc:
        logger.warning("redis_publish_failed", channel="alerts:live", error=str(exc))

    logger.info(
        "alert_created",
        alert_id=str(new_alert.id),
        threat_type=result.threat_type,
        severity=severity,
        confidence=result.confidence,
        latency_ms=latency_ms,
    )


# ── Redpanda consumer background task ────────────────────────────

async def consume_detector_results(
    session_factory: async_sessionmaker,
    redis: aioredis.Redis,
) -> None:
    """
    Long-running Kafka consumer that reads detector results from Redpanda
    and processes them through the alert engine pipeline.
    """
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=settings.redpanda_brokers,
        group_id="alert-engine",
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    try:
        await consumer.start()
        logger.info(
            "alert_engine_started",
            topic=TOPIC,
            brokers=settings.redpanda_brokers,
        )

        async for msg in consumer:
            try:
                result = DetectorResult(**msg.value)
                async with session_factory() as db:
                    await process_detector_result(db, redis, result)
            except ValidationError as exc:
                logger.error(
                    "invalid_detector_result",
                    errors=exc.errors(),
                    raw=msg.value,
                )
            except Exception as exc:
                logger.error(
                    "alert_engine_processing_error",
                    error=str(exc),
                    raw=msg.value,
                )

    except Exception as exc:
        logger.error("alert_engine_consumer_fatal", error=str(exc))
    finally:
        await consumer.stop()
        logger.info("alert_engine_consumer_stopped")
