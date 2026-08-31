import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)


class KafkaProducerService:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None

    async def start(self):
        """Start the producer connection."""
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
            )
            await self._producer.start()
            logger.info("Redpanda Producer started.")

    async def stop(self):
        """Stop the producer connection."""
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
            logger.info("Redpanda Producer stopped.")

    async def send_message(self, topic: str, src_ip: str, payload: dict[str, Any]):
        """
        Send a message to Redpanda.

        The raw canonical `src_ip` is used as the Kafka message key.
        We do NOT implement a second application-level hashing layer here.
        We rely on aiokafka's deterministic partitioner to route the same src_ip
        to the same partition.
        """
        if self._producer is None:
            raise RuntimeError("Producer is not started")

        key_bytes = src_ip.encode("utf-8")
        value_bytes = json.dumps(payload).encode("utf-8")

        await self._producer.send_and_wait(topic, key=key_bytes, value=value_bytes)
