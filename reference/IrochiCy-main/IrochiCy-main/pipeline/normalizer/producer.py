"""NormalizerProducer — Produces canonical events to Redpanda/Kafka topics.

Uses AIOKafkaProducer with LZ4 compression, idempotence, and dead-letter routing.
"""

from __future__ import annotations

import json
import time
from typing import Optional

import structlog
from aiokafka import AIOKafkaProducer

from normalizer.models import CanonicalEvent

logger = structlog.get_logger(__name__)

# Topic routing by event_type
TOPIC_MAP = {
    "connection": "canonical.connection",
    "dns": "canonical.dns",
    "tls": "canonical.tls",
}

DEAD_LETTER_TOPIC = "dead.letter"
METRICS_TOPIC = "pipeline.metrics"


class NormalizerProducer:
    """Produces canonical events to Redpanda with LZ4 compression and idempotence.

    Usage:
        async with NormalizerProducer("localhost:9092") as producer:
            await producer.produce_event(event)
    """

    def __init__(self, brokers: str = "localhost:9092") -> None:
        self.brokers = brokers
        self._producer: Optional[AIOKafkaProducer] = None
        self._produced_count = 0
        self._error_count = 0

    async def start(self) -> None:
        """Start the Kafka producer."""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.brokers,
            compression_type="gzip",
            linger_ms=5,
            acks="all",
            enable_idempotence=True,
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self._producer.start()
        logger.info("producer_started", brokers=self.brokers)

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer:
            await self._producer.stop()
            logger.info(
                "producer_stopped",
                produced=self._produced_count,
                errors=self._error_count,
            )

    async def __aenter__(self) -> NormalizerProducer:
        await self.start()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.stop()

    async def produce_event(self, event: CanonicalEvent) -> None:
        """Produce a canonical event to the appropriate topic.

        Routes by event_type → topic. Key is src_ip for partition affinity.
        On failure, produces to dead.letter.
        """
        assert self._producer is not None, "Producer not started"

        topic = TOPIC_MAP.get(event.event_type)
        if not topic:
            await self.produce_dead_letter(
                event.model_dump(mode="json"),
                f"Unknown event_type: {event.event_type}",
            )
            return

        try:
            await self._producer.send_and_wait(
                topic,
                key=event.src_ip,
                value=event.model_dump(mode="json"),
            )
            self._produced_count += 1
        except Exception as exc:
            logger.error(
                "produce_failed",
                topic=topic,
                event_id=event.event_id,
                error=str(exc),
            )
            self._error_count += 1
            await self.produce_dead_letter(
                event.model_dump(mode="json"),
                str(exc),
            )

    async def produce_dead_letter(self, raw: dict, error: str) -> None:
        """Produce a failed event to the dead.letter topic."""
        assert self._producer is not None, "Producer not started"

        dead_letter = {
            "original_payload": raw,
            "error": error,
            "timestamp": int(time.time() * 1_000_000),
            "original_topic": raw.get("event_type", "unknown"),
        }
        try:
            await self._producer.send_and_wait(
                DEAD_LETTER_TOPIC,
                key=raw.get("event_type", "unknown"),
                value=dead_letter,
            )
            logger.warning("dead_letter_produced", error=error)
        except Exception as exc:
            logger.error("dead_letter_failed", error=str(exc))

    async def produce_metrics(self, metrics: dict) -> None:
        """Produce pipeline metrics to the metrics topic."""
        assert self._producer is not None, "Producer not started"

        try:
            await self._producer.send_and_wait(
                METRICS_TOPIC,
                key=metrics.get("metric_name", "normalizer"),
                value=metrics,
            )
        except Exception as exc:
            logger.error("metrics_produce_failed", error=str(exc))

    @property
    def stats(self) -> dict:
        """Return producer stats."""
        return {
            "produced": self._produced_count,
            "errors": self._error_count,
        }
