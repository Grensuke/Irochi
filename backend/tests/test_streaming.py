import asyncio
import json
import uuid
import logging

import pytest
import pytest_asyncio


from app.core.config import REDPANDA_BROKER
from app.services.streaming.producer import KafkaProducerService
from app.services.streaming.consumer import KafkaConsumerService


logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def test_topic():
    """Returns the already-created connection topic for testing."""
    topic_name = "irochi.events.connection.v1"
    yield topic_name


@pytest.mark.asyncio
async def test_producer_and_consumer_integration(test_topic: str):
    """Test basic producer send and consumer receive loop."""
    producer = KafkaProducerService(bootstrap_servers=REDPANDA_BROKER)
    await producer.start()

    group_id = f"test.group.{uuid.uuid4().hex}"
    consumer = KafkaConsumerService(
        bootstrap_servers=REDPANDA_BROKER,
        group_id=group_id,
        topics=[test_topic]
    )
    await consumer.start()

    # Send a message
    test_src_ip = f"192.168.1.100-{uuid.uuid4().hex}"
    test_payload = {"event_id": "123", "data": "test_integration", "src_ip": test_src_ip}

    await producer.send_message(test_topic, test_src_ip, test_payload)

    # Consume the message
    consumed = False
    async for msg in consumer.consume():
        if msg.payload.get("src_ip") == test_src_ip:
            assert msg.topic == test_topic
            assert msg.payload["event_id"] == "123"
            assert msg.payload["data"] == "test_integration"

            # Verify new envelope fields
            assert msg.partition is not None
            assert msg.offset is not None
            assert msg.key.decode("utf-8") == test_src_ip

            consumed = True
            break  # We found our message

    assert consumed is True

    await producer.stop()
    await consumer.stop()


@pytest.mark.asyncio
async def test_deterministic_partition_routing(test_topic: str):
    """
    Test that:
    - The same src_ip deterministically maps to the same partition.
    - The raw src_ip is the message key (no second hashing layer).
    """
    producer = KafkaProducerService(bootstrap_servers=REDPANDA_BROKER)
    await producer.start()

    run_id = uuid.uuid4().hex
    src_ip_1 = f"10.0.0.1-{run_id}"
    src_ip_2 = f"192.168.1.50-{run_id}"

    # Send multiple messages for each src_ip
    for _ in range(5):
        await producer.send_message(test_topic, src_ip_1, {"src": src_ip_1, "run_id": run_id})
        await producer.send_message(test_topic, src_ip_2, {"src": src_ip_2, "run_id": run_id})

    # To inspect partitions and raw keys, we bypass the consumer wrapper
    # and use a raw AIOKafkaConsumer.
    from aiokafka import AIOKafkaConsumer

    raw_consumer = AIOKafkaConsumer(
        test_topic,
        bootstrap_servers=REDPANDA_BROKER,
        group_id=f"test.group.raw.{uuid.uuid4().hex}",
        auto_offset_reset="earliest"
    )
    await raw_consumer.start()

    partitions_for_ip1 = set()
    partitions_for_ip2 = set()
    messages_received = 0

    try:
        # We expect 10 messages total
        while messages_received < 10:
            msg = await asyncio.wait_for(raw_consumer.getone(), timeout=5.0)

            # 1. Verify the RAW src_ip is the message key
            raw_key = msg.key.decode("utf-8")

            # Only process messages belonging to this test run
            if raw_key not in (src_ip_1, src_ip_2):
                continue

            # 2. Track partitions
            if raw_key == src_ip_1:
                partitions_for_ip1.add(msg.partition)
            elif raw_key == src_ip_2:
                partitions_for_ip2.add(msg.partition)

            messages_received += 1

        # 3. Verify deterministic partition routing (same src_ip -> same partition)
        assert len(partitions_for_ip1) == 1, f"src_ip_1 mapped to multiple partitions: {partitions_for_ip1}"
        assert len(partitions_for_ip2) == 1, f"src_ip_2 mapped to multiple partitions: {partitions_for_ip2}"

    finally:
        await raw_consumer.stop()
        await producer.stop()


@pytest.mark.asyncio
async def test_consumer_skips_malformed_json(test_topic: str):
    """Test that malformed JSON payloads are caught and skipped."""
    # Send a malformed message bypassing the wrapper
    producer = KafkaProducerService(bootstrap_servers=REDPANDA_BROKER)
    await producer.start()

    run_id = uuid.uuid4().hex

    # Valid msg
    await producer.send_message(test_topic, "10.0.0.1", {"valid": True, "run_id": run_id})

    # Malformed msg (raw bytes)
    await producer._producer.send_and_wait(
        test_topic,
        key=b"10.0.0.2",
        value=b"this is not valid json"
    )

    # Valid msg
    await producer.send_message(test_topic, "10.0.0.3", {"valid": True, "run_id": run_id})
    await producer.stop()

    group_id = f"test.group.{uuid.uuid4().hex}"
    consumer = KafkaConsumerService(
        bootstrap_servers=REDPANDA_BROKER,
        group_id=group_id,
        topics=[test_topic]
    )
    await consumer.start()

    # Should only yield the two valid messages
    valid_count = 0
    try:
        async for msg in consumer.consume():
            if msg.payload.get("run_id") == run_id:
                assert msg.payload["valid"] is True
                valid_count += 1
                if valid_count == 2:
                    break
    except asyncio.TimeoutError:
        pass
    finally:
        await consumer.stop()

    assert valid_count == 2, "Consumer did not skip the malformed message properly"
