"""DetectorResultProducer — Publishes DetectorResults to detector.results topic."""

from __future__ import annotations

import json
from typing import Optional

import structlog
from aiokafka import AIOKafkaProducer

from detectors.result import DetectorResult

logger = structlog.get_logger(__name__)

TOPIC = "detector.results"


class DetectorResultProducer:
    """Produces DetectorResult dicts to the detector.results Redpanda topic."""

    def __init__(self, brokers: str = "localhost:9092") -> None:
        self.brokers = brokers
        self._producer: Optional[AIOKafkaProducer] = None

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
        logger.info("detector_producer_started", brokers=self.brokers)

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer:
            await self._producer.stop()
            logger.info("detector_producer_stopped")

    async def __aenter__(self) -> DetectorResultProducer:
        await self.start()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.stop()

    async def produce_result(self, result: DetectorResult) -> None:
        """Produce a detector result to the detector.results topic."""
        assert self._producer is not None, "Producer not started"

        try:
            await self._producer.send_and_wait(
                TOPIC,
                key=result.threat_type,
                value=result.model_dump(mode="json"),
            )
            logger.info(
                "detection_produced",
                threat_type=result.threat_type,
                confidence=result.confidence,
                src_ip=result.src_ip,
            )
        except Exception as exc:
            logger.error("detection_produce_failed", error=str(exc))
