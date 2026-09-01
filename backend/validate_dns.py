import asyncio
import logging
import json
from aiokafka import AIOKafkaConsumer

from app.schemas.canonical import CanonicalEvent, EventType
from app.services.streaming.consumer import ConsumerMessage
from app.services.features.engine import FeatureEngine
from app.services.features.state import FeatureStateAdapter
from app.services.state.redis_client import RedisStateService
from app.services.detectors.router import DetectorRouter
from app.services.detectors.registry import DetectorRegistry
from app.services.detectors.grouping import GroupingInterface
from app.schemas.detectors import DetectorInput, DetectorId, Decision
from app.services.detectors.dns import DnsDetector

import redis.asyncio as aioredis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PassThroughGrouping(GroupingInterface):
    async def add_and_evaluate(self, detector_input: DetectorInput) -> list:
        return [detector_input]
    def get_base_grouping_identity(self, detector_input: DetectorInput) -> str:
        return ""

async def main():
    # 1. Setup Redis State
    state_service = RedisStateService("redis://localhost:6379/0")
    await state_service.start()
    state_adapter = FeatureStateAdapter(state_service)

    # 2. Setup Feature Engine
    feature_engine = FeatureEngine(state_adapter)

    # 3. Setup Detector Framework
    registry = DetectorRegistry()

    dns_detector = DnsDetector()
    registry.register(dns_detector)

    router = DetectorRouter(registry, PassThroughGrouping())

    # 4. Setup Redpanda Consumer
    consumer = AIOKafkaConsumer(
        "irochi.events.dns.v1",
        bootstrap_servers='localhost:19092',
        group_id="validate-dns-group",
        auto_offset_reset="earliest"
    )

    await consumer.start()
    logger.info("Connected to Redpanda. Listening for DNS events...")

    processed = 0
    detections = 0
    errors = 0

    from pydantic import TypeAdapter
    event_adapter = TypeAdapter(CanonicalEvent)

    try:
        async for msg in consumer:
            raw = json.loads(msg.value)
            cmsg = ConsumerMessage(
                topic=msg.topic,
                partition=msg.partition,
                offset=msg.offset,
                key=msg.key,
                payload=raw
            )

            # WP-D: Feature Engine
            feature_records = await feature_engine.process(cmsg)

            # WP-E/F: Detector Router & DNS Detector
            for record in feature_records:
                if record.detector_domain.value == "dns":
                    outputs = await router.route(record)

                    for out in outputs:
                        processed += 1
                        if out.decision == Decision.DETECTION:
                            detections += 1
                            logger.info(f"[DETECTION] DNS/DGA Tunnel: {out.entity_key} -> Score: {out.score:.4f}")
                        elif out.decision == Decision.DETECTOR_ERROR:
                            errors += 1
                            logger.error(f"[ERROR] {out.evidence}")

            if processed > 0 and processed % 1000 == 0:
                logger.info(f"Processed {processed} DNS records. Detections: {detections}")

    except KeyboardInterrupt:
        logger.info("Stopping validation...")
    except Exception as e:
        logger.error(f"Error during validation: {e}", exc_info=True)
    finally:
        await consumer.stop()
        await state_service.stop()
        logger.info(f"Summary: {processed} processed, {detections} detections, {errors} errors")

if __name__ == "__main__":
    asyncio.run(main())
