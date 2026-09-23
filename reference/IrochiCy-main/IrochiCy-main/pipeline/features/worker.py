"""Feature Worker — Orchestrator consuming canonical events and running detectors.

Consumes all 3 canonical topics from Redpanda, runs applicable detectors
per event type, and emits DetectorResults via DetectorResultProducer.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Optional

import structlog
from aiokafka import AIOKafkaConsumer

from detectors.ddos import DDoSDetector
from detectors.dns_dga import DnsDgaDetector
from detectors.exfil import ExfilDetector
from detectors.producer import DetectorResultProducer
from detectors.recon import ReconDetector
from detectors.tls_c2 import TlsC2Detector
from features.redis_state import RedisHotState
from intel.sslbl import sslbl_feed
from normalizer.models.connection import CanonicalConnectionEvent
from normalizer.models.dns import CanonicalDnsEvent
from normalizer.models.tls import CanonicalTlsEvent

logger = structlog.get_logger(__name__)

TOPICS = ["canonical.connection", "canonical.dns", "canonical.tls"]

# Event type → Pydantic model
EVENT_MODELS = {
    "connection": CanonicalConnectionEvent,
    "dns": CanonicalDnsEvent,
    "tls": CanonicalTlsEvent,
}


class FeatureWorker:
    """Consumes canonical events, runs detectors, emits DetectorResults."""

    def __init__(
        self,
        brokers: str = "localhost:9092",
        redis_url: str = "redis://:12345678@localhost:6379/0",
        group_id: str = "feature-workers",
    ) -> None:
        self.brokers = brokers
        self.redis_url = redis_url
        self.group_id = group_id
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._det_producer: Optional[DetectorResultProducer] = None
        self._redis_state: Optional[RedisHotState] = None
        self._event_count = 0
        self._detection_count = 0

        # Initialize detectors
        self.detector_map = {
            "connection": [DDoSDetector(), ReconDetector(), ExfilDetector()],
            "dns": [DnsDgaDetector()],
            "tls": [TlsC2Detector()],
        }

    async def start(self) -> None:
        """Start consumer, producer, and Redis connection."""
        # Load SSLBL feed
        await sslbl_feed.ensure_loaded()

        # Redis
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(self.redis_url)
        self._redis_state = RedisHotState(redis_client)
        await self._redis_state.set_detectors_active(5)

        # Kafka consumer
        self._consumer = AIOKafkaConsumer(
            *TOPICS,
            bootstrap_servers=self.brokers,
            group_id=self.group_id,
            auto_offset_reset="latest",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        await self._consumer.start()

        # Detector result producer
        self._det_producer = DetectorResultProducer(self.brokers)
        await self._det_producer.start()

        logger.info(
            "feature_worker_started",
            topics=TOPICS,
            group_id=self.group_id,
        )

    async def stop(self) -> None:
        """Stop consumer and producer."""
        if self._consumer:
            await self._consumer.stop()
        if self._det_producer:
            await self._det_producer.stop()
        logger.info(
            "feature_worker_stopped",
            events_processed=self._event_count,
            detections=self._detection_count,
        )

    async def run(self) -> None:
        """Main event loop — consume and process messages."""
        await self.start()
        try:
            async for msg in self._consumer:
                await self._process_message(msg)
        except KeyboardInterrupt:
            logger.info("feature_worker_interrupted")
        finally:
            await self.stop()

    async def _process_message(self, msg) -> None:
        """Process a single Kafka message."""
        start_time = time.time()

        try:
            data = msg.value
            event_type = data.get("event_type")
            if not event_type:
                return

            # Parse into typed Pydantic model
            model_cls = EVENT_MODELS.get(event_type)
            if not model_cls:
                return

            event = model_cls(**data)

            # Update EPS
            if self._redis_state:
                await self._redis_state.increment_events_per_second(event_type)

            self._event_count += 1

            # Run applicable detectors
            detectors = self.detector_map.get(event_type, [])
            for detector in detectors:
                try:
                    result = await detector.process_event(
                        event, {}, self._redis_state,
                    )
                    if result and self._det_producer:
                        await self._det_producer.produce_result(result)
                        self._detection_count += 1
                except Exception as exc:
                    logger.error(
                        "detector_error",
                        detector_id=detector.detector_id,
                        error=str(exc),
                    )

                # Refresh detector status every 10 events
                if self._event_count % 10 == 0 and self._redis_state:
                    await self._redis_state.set_detector_status(
                        detector.threat_type, "running",
                    )

            # Record latency
            latency_ms = int((time.time() - start_time) * 1000)
            if self._redis_state:
                await self._redis_state.record_detection_latency(latency_ms)

        except Exception as exc:
            logger.error("message_processing_error", error=str(exc))


async def main() -> None:
    """CLI entrypoint for the feature worker."""
    import argparse

    parser = argparse.ArgumentParser(description="SIH26145 Feature Worker")
    parser.add_argument("--brokers", default="localhost:9092")
    parser.add_argument("--redis-url", default="redis://:12345678@localhost:6379/0")
    parser.add_argument("--group-id", default="feature-workers")
    args = parser.parse_args()

    worker = FeatureWorker(
        brokers=args.brokers,
        redis_url=args.redis_url,
        group_id=args.group_id,
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
