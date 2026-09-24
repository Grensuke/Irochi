import asyncio
import logging
import os
import socket
import subprocess

from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError

logger = logging.getLogger(__name__)

TOPICS = [
    "vibhinetra.events.connection.v1",
    "vibhinetra.events.dns.v1",
    "vibhinetra.events.tls.v1",
]


def resolve_broker() -> str:
    candidate = os.environ.get("REDPANDA_BROKER")
    if candidate:
        host = candidate.split(":")[0]
        try:
            socket.gethostbyname(host)
            return candidate
        except socket.gaierror:
            pass
    return "localhost:19092"


async def setup_topics_via_admin(broker: str) -> bool:
    """Creates topics directly via Kafka protocol using AIOKafkaAdminClient."""
    admin = None
    try:
        admin = AIOKafkaAdminClient(bootstrap_servers=broker)
        await admin.start()
        existing = await admin.list_topics()
        new_topics = []
        for topic in TOPICS:
            if topic not in existing:
                new_topics.append(NewTopic(name=topic, num_partitions=3, replication_factor=1))

        if new_topics:
            logger.info(f"Creating topics via Kafka Admin API: {[t.name for t in new_topics]}")
            await admin.create_topics(new_topics)
        for topic in TOPICS:
            logger.info(f"Topic {topic} is ready.")
        return True
    except TopicAlreadyExistsError:
        for topic in TOPICS:
            logger.info(f"Topic {topic} is ready.")
        return True
    except Exception as e:
        logger.debug(f"Kafka Admin API attempt failed: {e}")
        return False
    finally:
        if admin:
            try:
                await admin.close()
            except Exception:
                pass


def setup_topics_via_docker() -> bool:
    """Fallback method using docker exec rpk."""
    container_name = "vibhinetra-redpanda"
    failed = False
    for topic in TOPICS:
        try:
            result = subprocess.run(
                [
                    "docker", "exec", container_name,
                    "rpk", "topic", "create", topic,
                    "-p", "3",
                    "-r", "1",
                ],
                capture_output=True,
                text=True,
            )
            combined_output = (result.stdout + " " + result.stderr).lower()
            if (
                result.returncode == 0
                or "already exists" in combined_output
                or "already_exists" in combined_output
                or "already been created" in combined_output
            ):
                logger.info(f"Topic {topic} is ready.")
            else:
                logger.error(f"Failed to create topic {topic}: {result.stderr or result.stdout}")
                failed = True
        except Exception as e:
            logger.error(f"Failed to execute docker command: {e}")
            failed = True
    return not failed


def setup_topics():
    broker = resolve_broker()
    logger.info(f"Bootstrapping raw event topics on {broker}...")
    try:
        success = asyncio.run(setup_topics_via_admin(broker))
        if success:
            return
    except Exception:
        pass

    logger.info("Falling back to docker exec rpk method...")
    if not setup_topics_via_docker():
        raise SystemExit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_topics()
