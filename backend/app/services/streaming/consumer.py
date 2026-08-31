import json
import logging
from typing import Any, AsyncGenerator

from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)


class KafkaConsumerService:
    def __init__(self, bootstrap_servers: str, group_id: str, topics: list[str]):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self):
        """Start the consumer connection."""
        if self._consumer is None:
            self._consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset="earliest",
            )
            await self._consumer.start()
            logger.info(f"Redpanda Consumer started for topics: {self.topics}")

    async def stop(self):
        """Stop the consumer connection."""
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None
            logger.info("Redpanda Consumer stopped.")

    async def consume(self) -> AsyncGenerator[tuple[str, dict[str, Any]], None]:
        """
        Yields (topic, payload) for each valid message.
        Malformed JSON payloads are safely skipped.
        """
        if self._consumer is None:
            raise RuntimeError("Consumer is not started")

        async for msg in self._consumer:
            try:
                payload = json.loads(msg.value.decode("utf-8"))
                yield msg.topic, payload
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as e:
                logger.warning(
                    f"Skipping malformed message on topic {msg.topic}: {e} (DEVELOPMENT CONFIG DLQ)"
                )
                continue
