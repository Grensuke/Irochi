"""
Vibhinetra Tape Playback Service
================================
Replays captured real network traffic (JSONL) through Redpanda.
Supports one-shot playback or continuous looping for deployments.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import socket
import time
from typing import Optional

from aiokafka import AIOKafkaProducer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("playback_demo")

TAPE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "real_demo_traffic.jsonl")


def resolve_broker(requested_broker: Optional[str] = None) -> str:
    candidate = requested_broker or os.environ.get("REDPANDA_BROKER")
    if candidate:
        host = candidate.split(":")[0]
        try:
            socket.gethostbyname(host)
            return candidate
        except socket.gaierror:
            pass
    return "localhost:19092"


async def playback_tape(
    broker: Optional[str] = None,
    events_per_second: int = 50,
    loop_forever: bool = False,
):
    resolved_broker = resolve_broker(broker)
    logger.info(f"Loading JSONL tape from: {TAPE_FILE}")
    if not os.path.exists(TAPE_FILE):
        logger.error(f"Tape file not found at: {TAPE_FILE}")
        return

    events = []
    with open(TAPE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(line.strip())

    logger.info(f"Loaded {len(events)} events from tape. Target broker: {resolved_broker}")
    mode = "CONTINUOUS LOOP" if loop_forever else "ONE-SHOT"
    logger.info(f"Mode: {mode} | Rate: {events_per_second} events/sec")

    producer = None
    for attempt in range(1, 15):
        try:
            producer = AIOKafkaProducer(bootstrap_servers=resolved_broker)
            await producer.start()
            break
        except Exception as e:
            logger.warning(f"Connection attempt {attempt}/15 failed: {e}")
            await asyncio.sleep(2.0)

    if not producer:
        logger.error("Could not connect to Kafka broker. Exiting.")
        return

    stop_event = asyncio.Event()

    def request_stop():
        logger.info("Stop requested. Gracefully shutting down...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_stop)
        except (NotImplementedError, RuntimeError):
            pass

    sleep_interval = 1.0 / max(1, events_per_second)
    cycle = 0

    try:
        while not stop_event.is_set():
            cycle += 1
            start_time = time.time()
            if loop_forever and cycle > 1:
                logger.info(f"Starting tape replay cycle #{cycle}...")

            for i, event_str in enumerate(events):
                if stop_event.is_set():
                    break

                # Parse and refresh ingest timestamp to keep data current
                evt = json.loads(event_str)
                evt["ingest_timestamp"] = int(time.time() * 1000000)

                await producer.send_and_wait(
                    "vibhinetra.events.connection.v1", json.dumps(evt).encode("utf-8")
                )

                if (i + 1) % 200 == 0:
                    logger.info(f"Cycle {cycle}: Played {i + 1} / {len(events)} events...")

                await asyncio.sleep(sleep_interval)

            elapsed = time.time() - start_time
            logger.info(f"Cycle {cycle} complete: {len(events)} events played in {elapsed:.2f}s.")

            if not loop_forever:
                break

    finally:
        if producer:
            await producer.stop()
            logger.info("Kafka producer stopped cleanly.")


def main():
    parser = argparse.ArgumentParser(description="Vibhinetra Traffic Tape Playback")
    parser.add_argument(
        "--loop",
        action="store_true",
        default=os.environ.get("LOOP_FOREVER", "false").lower() in ("true", "1", "yes"),
        help="Continuously loop playback (default: False)",
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=int(os.environ.get("EVENTS_PER_SECOND", "50")),
        help="Events per second (default: 50)",
    )
    parser.add_argument(
        "--broker",
        type=str,
        default=os.environ.get("REDPANDA_BROKER", None),
        help="Broker address (default: auto-detect)",
    )
    args = parser.parse_args()

    asyncio.run(
        playback_tape(
            broker=args.broker,
            events_per_second=args.rate,
            loop_forever=args.loop,
        )
    )


if __name__ == "__main__":
    main()
