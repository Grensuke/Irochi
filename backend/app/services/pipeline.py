import logging
import asyncio
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.streaming.consumer import KafkaConsumerService
from app.services.features.engine import FeatureEngine
from app.services.detectors.router import DetectorRouter
from app.services.alert_engine import AlertEngine
from app.services.postgres_alert_service import PostgresAlertService
from app.services.redis_pubsub import RedisPubSubService

logger = logging.getLogger(__name__)


class DetectionPipeline:
    """
    Application-level orchestrator connecting Redpanda consumption, feature extraction,
    detector routing, and persistence.
    """

    def __init__(
        self,
        consumer: KafkaConsumerService,
        feature_engine: FeatureEngine,
        router: DetectorRouter,
        session_factory: Callable[[], AsyncSession],
        redis_service: RedisPubSubService,
    ):
        self.consumer = consumer
        self.feature_engine = feature_engine
        self.router = router
        self.session_factory = session_factory
        self.redis_service = redis_service
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self):
        """Starts the pipeline orchestrator loop in a background task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("DetectionPipeline started.")

    async def stop(self):
        """Stops the pipeline orchestrator loop cleanly."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("DetectionPipeline stopped.")

    async def _run_loop(self):
        """Main orchestrator execution loop."""
        try:
            async for message in self.consumer.consume():
                if not self._running:
                    break

                try:
                    await self._process_message(message)
                except Exception as e:
                    # One bad message or processing fault MUST NOT kill the consumer loop
                    logger.error(
                        f"Unhandled error processing message from topic={message.topic} "
                        f"partition={message.partition} offset={message.offset}: {e}",
                        exc_info=True
                    )
        except asyncio.CancelledError:
            logger.info("DetectionPipeline loop cancelled.")
        except Exception as e:
            # Task-level exception handler to ensure catastrophic programming errors are logged
            logger.critical(f"DetectionPipeline loop terminated unexpectedly: {e}", exc_info=True)
            raise

    async def _process_message(self, message):
        """Processes a single ConsumerMessage through the pipeline engines."""

        # 1. Feature Extraction
        feature_records = await self.feature_engine.process(message)
        if not feature_records:
            return

        for record in feature_records:
            # 2. Detector Routing
            detector_outputs = await self.router.route(record)
            if not detector_outputs:
                continue

            for output in detector_outputs:
                # 3. Alert Persistence and Redis Publish
                # Create a fresh database session scope per alert output
                async with self.session_factory() as session:
                    pg_service = PostgresAlertService(session)
                    alert_engine = AlertEngine(
                        postgres_service=pg_service,
                        redis_service=self.redis_service
                    )

                    try:
                        await alert_engine.process_detector_output(output)
                    except Exception as e:
                        logger.error(
                            f"Error persisting detector output {output.output_id} "
                            f"from detector {output.detector_id.value}: {e}",
                            exc_info=True
                        )
