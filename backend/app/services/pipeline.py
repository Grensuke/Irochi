import logging
import asyncio
import time
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.detectors import Decision, DetectorId

from app.services.streaming.consumer import KafkaConsumerService
from app.services.features.engine import FeatureEngine
from app.services.detectors.router import DetectorRouter
from app.services.alert_engine import AlertEngine
from app.services.incident_engine import IncidentEngine
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
        
        # Live Telemetry State
        self._last_telemetry_publish = time.time()
        self._telemetry_flows = 0
        self._telemetry_bytes = 0
        self._telemetry_sample_events = []
        self._recent_detections = {}

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

                # Live Telemetry Tracking
                self._telemetry_flows += 1
                inner_payload = message.payload.get("payload", {})
                self._telemetry_bytes += inner_payload.get("orig_bytes", 0) + inner_payload.get("resp_bytes", 0)
                
                if len(self._telemetry_sample_events) < 5:
                    self._telemetry_sample_events.append(message.payload)
                
                now = time.time()
                if now - self._last_telemetry_publish >= 1.0:
                    stats = {
                        "flows_per_sec": self._telemetry_flows,
                        "bytes_per_sec": self._telemetry_bytes,
                        "events": self._telemetry_sample_events
                    }
                    # Fire and forget publish
                    asyncio.create_task(self.redis_service.publish_telemetry(stats))
                    
                    self._last_telemetry_publish = now
                    self._telemetry_flows = 0
                    self._telemetry_bytes = 0
                    self._telemetry_sample_events = []

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
        t0 = time.time()
        feature_records = await self.feature_engine.process(message)
        t1 = time.time()
        
        router_total_time = 0
        
        if feature_records:
            for record in feature_records:
                # 2. Detector Routing
                t2 = time.time()
                detector_outputs = await self.router.route(record)
                t3 = time.time()
                router_total_time += (t3 - t2)
                
                if not detector_outputs:
                    continue

                for output in detector_outputs:
                    if output.decision != Decision.DETECTION:
                        continue

                    # Pipeline-level debounce to prevent DB session overhead
                    cache_key = (output.detector_id, output.entity_key)
                    now = time.time()
                    if now - self._recent_detections.get(cache_key, 0) < 5.0:
                        continue
                    self._recent_detections[cache_key] = now

                    # 3. Alert Persistence and Redis Publish
                    # Create a fresh database session scope ONLY for actual detections
                    async with self.session_factory() as session:
                        pg_service = PostgresAlertService(session)
                        alert_engine = AlertEngine(
                            postgres_service=pg_service,
                            redis_service=self.redis_service
                        )
                        incident_engine = IncidentEngine()

                        try:
                            alert_payload = await alert_engine.process_detector_output(output)
                            if alert_payload:
                                await incident_engine.on_alert(alert_payload, session)
                        except Exception as e:
                            logger.error(
                                f"Error persisting detector output {output.output_id} "
                                f"from detector {output.detector_id.value}: {e}",
                                exc_info=True
                            )
                        
        total_time = time.time() - t0
        if total_time > 0.05:
            logger.info(f"DEBUG PIPELINE TIMING: Total message processing took {total_time*1000:.2f}ms (Feature: {(t1-t0)*1000:.2f}ms, Router sum: {router_total_time*1000:.2f}ms). Event Type: {message.payload.get('event_type')}")
