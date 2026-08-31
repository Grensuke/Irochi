import asyncio
import logging
import json
from aiokafka import AIOKafkaConsumer

from app.schemas.canonical import CanonicalEvent
from app.services.streaming.consumer import ConsumerMessage
from app.services.features.engine import FeatureEngine
from app.services.features.state import FeatureStateAdapter
from app.services.state.redis_client import RedisStateService
from app.services.detectors.router import DetectorRouter
from app.services.detectors.registry import DetectorRegistry
from app.services.detectors.grouping import GroupingInterface
from app.schemas.detectors import DetectorInput, DetectorId, Decision
from app.services.detectors.recon import ReconDetector

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

    # DEVELOPMENT THRESHOLD: We set it artificially low (e.g., 2) to trigger on the Friday sample
    # since this sample might not contain the massive afternoon PortScan.
    recon_detector = ReconDetector(portscan_threshold=2)
    registry.register(recon_detector)

    router = DetectorRouter(registry, PassThroughGrouping())

    # 4. Setup Redpanda Consumer
    consumer = AIOKafkaConsumer(
        "irochi.events.connection.v1",
        bootstrap_servers='localhost:19092',
        group_id="validate-recon-group",
        auto_offset_reset="earliest"
    )

    await consumer.start()

    logger.info("Listening to Redpanda for Recon validation...")

    detections = 0
    total_messages = 0

    try:
        # We will process a bounded number of messages to prove the pipeline
        while total_messages < 2000 and detections == 0:
            msg = await asyncio.wait_for(consumer.getone(), timeout=5.0)
            total_messages += 1

            if not msg.value:
                continue
            payload = json.loads(msg.value.decode('utf-8'))
            cmsg = ConsumerMessage(
                topic=msg.topic,
                partition=msg.partition,
                offset=msg.offset,
                key=msg.key.decode('utf-8') if msg.key else None,
                payload=payload
            )

            # WP-D
            records = await feature_engine.process(cmsg)

            # WP-E
            for record in records:
                if record.detector_domain.value == "recon":
                    outputs = await router.route(record)
                    for out in outputs:
                        if out.decision == Decision.DETECTION:
                            logger.info(f"DETECTION! Source IP {out.entity_key} scanned {out.score} ports.")
                            logger.info(f"Output: {out.model_dump_json(indent=2)}")
                            detections += 1
                            break
    except asyncio.TimeoutError:
        logger.info("Timeout waiting for messages. Finished.")
    finally:
        await consumer.stop()
        await state_service.stop()

    if detections > 0:
        logger.info(f"Validation successful! Reached ReconDetector. Processed {total_messages} messages.")
    else:
        logger.info(f"No detections found. Processed {total_messages} messages.")

if __name__ == "__main__":
    asyncio.run(main())
