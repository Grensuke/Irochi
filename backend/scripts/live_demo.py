"""
Vibhinetra Live Data Generator
==============================
Continuously generates realistic synthetic network telemetry and threat scenarios
(benign traffic, C2 beaconing, DGA DNS tunneling, data exfiltration, volumetric DDoS,
port reconnaissance, and TLS sessions) in an infinite streaming loop for live deployment
and demonstrations.

Configurable via CLI arguments or Environment Variables:
  - LOOP_FOREVER: "true" / "1" (default: True, continuous infinite loop)
  - DURATION_SECONDS: int (0 or negative = run forever; positive = stop after N seconds)
  - TICK_INTERVAL: float (seconds between ticks, default: 1.0)
  - REDPANDA_BROKER: kafka/redpanda broker address (default: auto-detected)
"""

import asyncio
import json
import logging
import os
import random
import signal
import socket
import sys
import time
from typing import Optional

from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import KafkaConnectionError, TopicAlreadyExistsError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("live_demo")

# Required Kafka / Redpanda Topics
REQUIRED_TOPICS = [
    "vibhinetra.events.connection.v1",
    "vibhinetra.events.dns.v1",
    "vibhinetra.events.tls.v1",
]


def resolve_broker(requested_broker: Optional[str] = None) -> str:
    """
    Intelligently resolves broker address.
    Checks environment or requested parameter, testing if host resolves.
    Falls back to localhost:19092 if running outside docker container.
    """
    candidate = requested_broker or os.environ.get("REDPANDA_BROKER")
    if candidate:
        host = candidate.split(":")[0]
        try:
            socket.gethostbyname(host)
            return candidate
        except socket.gaierror:
            logger.warning(
                f"Broker host '{host}' does not resolve in DNS. Falling back to localhost:19092."
            )
    return "localhost:19092"


async def ensure_topics(broker: str, max_retries: int = 20, retry_delay: float = 2.0):
    """
    Ensures required Kafka topics exist before producing.
    Retries until Redpanda/Kafka broker is ready.
    """
    logger.info(f"Connecting to broker at {broker} to verify/create topics...")
    admin = None
    for attempt in range(1, max_retries + 1):
        try:
            admin = AIOKafkaAdminClient(bootstrap_servers=broker)
            await admin.start()
            existing_topics = await admin.list_topics()

            new_topics = []
            for topic in REQUIRED_TOPICS:
                if topic not in existing_topics:
                    new_topics.append(NewTopic(name=topic, num_partitions=3, replication_factor=1))

            if new_topics:
                logger.info(f"Creating missing topics: {[t.name for t in new_topics]}")
                try:
                    await admin.create_topics(new_topics)
                    logger.info("Topics created successfully.")
                except TopicAlreadyExistsError:
                    pass
            else:
                logger.info("All required event topics are verified ready.")
            return True
        except Exception as e:
            logger.warning(f"Waiting for broker at {broker} (attempt {attempt}/{max_retries}): {e}")
            await asyncio.sleep(retry_delay)
        finally:
            if admin:
                try:
                    await admin.close()
                except Exception:
                    pass

    logger.error(f"Failed to connect to broker at {broker} after {max_retries} attempts.")
    return False


async def send_connection(
    producer: AIOKafkaProducer,
    src: str,
    dst: str,
    ts: int,
    src_port: Optional[int] = None,
    dst_port: int = 443,
    orig_bytes: int = 100,
    resp_bytes: int = 200,
    conn_state: str = "SF",
    history: str = "ShADadFf",
):
    event = {
        "event_id": f"evt-{ts}-{random.randint(1000, 9999)}",
        "connection_id": f"conn-{src}-{dst}:{dst_port}",
        "timestamp": ts * 1000000,
        "timestamp_precision": "microsecond",
        "ingest_timestamp": int(time.time() * 1000000),
        "sensor_source": "zeek",
        "src_ip": src,
        "dst_ip": dst,
        "src_port": src_port or random.randint(1024, 65535),
        "dst_port": dst_port,
        "protocol": "tcp",
        "schema_version": "1.0.0",
        "event_type": "connection",
        "payload": {
            "orig_bytes": orig_bytes,
            "resp_bytes": resp_bytes,
            "orig_pkts": max(1, orig_bytes // 1000),
            "resp_pkts": max(1, resp_bytes // 1000),
            "conn_state": conn_state,
            "history": history,
        },
    }
    await producer.send_and_wait(
        "vibhinetra.events.connection.v1", json.dumps(event).encode("utf-8")
    )


async def send_dns(
    producer: AIOKafkaProducer,
    src: str,
    query: str,
    ts: int,
    qtype: str = "A",
    rcode: str = "NOERROR",
    answers: Optional[list] = None,
):
    event = {
        "event_id": f"evt-{ts}-{random.randint(1000, 9999)}",
        "connection_id": f"conn-{src}-8.8.8.8:53",
        "timestamp": ts * 1000000,
        "timestamp_precision": "microsecond",
        "ingest_timestamp": int(time.time() * 1000000),
        "sensor_source": "zeek",
        "src_ip": src,
        "dst_ip": "8.8.8.8",
        "src_port": random.randint(1024, 65535),
        "dst_port": 53,
        "protocol": "udp",
        "schema_version": "1.0.0",
        "event_type": "dns",
        "payload": {
            "query": query,
            "qtype_name": qtype,
            "rcode_name": rcode,
            "answers": answers or ["192.168.1.1"],
        },
    }
    await producer.send_and_wait(
        "vibhinetra.events.dns.v1", json.dumps(event).encode("utf-8")
    )


async def send_tls(
    producer: AIOKafkaProducer,
    src: str,
    dst: str,
    server_name: str,
    ts: int,
    ja3: str = "e7d705a3286e19ea42f587b344ee6865",
):
    event = {
        "event_id": f"evt-tls-{ts}-{random.randint(1000, 9999)}",
        "connection_id": f"conn-{src}-{dst}:443",
        "timestamp": ts * 1000000,
        "timestamp_precision": "microsecond",
        "ingest_timestamp": int(time.time() * 1000000),
        "sensor_source": "zeek",
        "src_ip": src,
        "dst_ip": dst,
        "src_port": random.randint(1024, 65535),
        "dst_port": 443,
        "protocol": "tcp",
        "schema_version": "1.0.0",
        "event_type": "tls",
        "payload": {
            "ja3": ja3,
            "server_name": server_name,
        },
    }
    await producer.send_and_wait(
        "vibhinetra.events.tls.v1", json.dumps(event).encode("utf-8")
    )


async def send_recon_scan(
    producer: AIOKafkaProducer, attacker_ip: str, target_ip: str, ts: int
):
    """Generates a rapid multi-port TCP SYN sweep against a target IP."""
    target_ports = random.sample(
        [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 1433, 3306, 3389, 5432, 8080, 8443],
        k=random.randint(6, 12),
    )
    for port in target_ports:
        await send_connection(
            producer=producer,
            src=attacker_ip,
            dst=target_ip,
            ts=ts,
            dst_port=port,
            orig_bytes=60,
            resp_bytes=0,
            conn_state="S0",
            history="S",
        )


async def run_live_demo(
    broker: Optional[str] = None,
    duration_seconds: int = 0,
    tick_interval: float = 1.0,
    loop_forever: bool = True,
):
    """
    Main live telemetry generation loop.
    Runs indefinitely when loop_forever is True (or duration_seconds <= 0).
    """
    resolved_broker = resolve_broker(broker)

    # 1. Ensure topics exist and broker is reachable
    topics_ready = await ensure_topics(resolved_broker)
    if not topics_ready:
        logger.error("Aborting live generator: broker not ready.")
        return

    # 2. Start Producer with retry
    logger.info(f"Starting AIOKafkaProducer connecting to {resolved_broker}...")
    producer = None
    for attempt in range(1, 15):
        try:
            producer = AIOKafkaProducer(bootstrap_servers=resolved_broker)
            await producer.start()
            break
        except Exception as e:
            logger.warning(f"Producer connection attempt {attempt}/15 failed: {e}")
            await asyncio.sleep(2.0)

    if not producer:
        logger.error("Could not start Kafka producer. Exiting.")
        return

    mode_str = "INFINITE LOOP (24/7 continuous stream)" if loop_forever or duration_seconds <= 0 else f"{duration_seconds}s run"
    logger.info(f"Live Traffic Generator started in {mode_str} [Tick: {tick_interval}s]")

    # Stats tracking
    stats = {
        "connections": 0,
        "dns": 0,
        "tls": 0,
        "c2": 0,
        "exfil": 0,
        "ddos": 0,
        "recon": 0,
    }
    total_events = 0
    start_time = time.time()
    last_stat_time = time.time()

    # Graceful stop handle
    stop_event = asyncio.Event()

    def request_stop():
        logger.info("Shutdown signal received. Stopping live data generator...")
        stop_event.set()

    # Register OS signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_stop)
        except (NotImplementedError, RuntimeError):
            # Windows signal handling fallback
            pass

    try:
        iteration = 0
        while not stop_event.is_set():
            iteration += 1
            now = int(time.time())

            # Check duration limit if not looping forever
            if not loop_forever and duration_seconds > 0:
                if (time.time() - start_time) >= duration_seconds:
                    logger.info(f"Target duration of {duration_seconds}s reached.")
                    break

            # -------------------------------------------------------------
            # 1. Background Normal Traffic (2 to 6 random benign flows)
            # -------------------------------------------------------------
            for _ in range(random.randint(2, 6)):
                src = f"192.168.1.{random.randint(10, 80)}"
                dst = f"10.0.0.{random.randint(1, 200)}"
                orig_b = random.randint(100, 4000)
                resp_b = random.randint(200, 30000)
                await send_connection(producer, src, dst, now, orig_bytes=orig_b, resp_bytes=resp_b)
                stats["connections"] += 1
                total_events += 1

                # Normal TLS handshake for some connections
                if random.random() < 0.4:
                    benign_domains = ["api.github.com", "login.microsoftonline.com", "cdn.cloudflare.net", "aws.amazon.com"]
                    await send_tls(producer, src, dst, random.choice(benign_domains), now)
                    stats["tls"] += 1
                    total_events += 1

            # -------------------------------------------------------------
            # 2. C2 Beaconing (Regular periodic heartbeat to attacker C2)
            # -------------------------------------------------------------
            if random.random() < 0.85:
                # Compromised workstation 1
                await send_connection(producer, "192.168.1.15", "198.51.100.45", now, dst_port=443, orig_bytes=148, resp_bytes=152)
                await send_tls(producer, "192.168.1.15", "198.51.100.45", "sync.cloud-telemetry.org", now, ja3="72a589da586844d7f0818ce684948eea")
                stats["c2"] += 2
                total_events += 2

            if random.random() < 0.65:
                # Compromised workstation 2
                await send_connection(producer, "192.168.1.22", "198.51.100.99", now, dst_port=8443, orig_bytes=124, resp_bytes=128)
                stats["c2"] += 1
                total_events += 1

            # -------------------------------------------------------------
            # 3. DGA / DNS Tunneling (Pseudo-random domain query)
            # -------------------------------------------------------------
            if random.random() < 0.50:
                dga_len = random.randint(12, 20)
                dga_domain = f"{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=dga_len))}.biz"
                await send_dns(producer, "192.168.1.15", dga_domain, now)
                stats["dns"] += 1
                total_events += 1

            # -------------------------------------------------------------
            # 4. Recon / Port Scanning (Periodic reconnaissance bursts)
            # -------------------------------------------------------------
            if random.random() < 0.20:
                attacker = f"203.0.113.{random.randint(10, 50)}"
                target = f"10.0.0.{random.randint(1, 10)}"
                await send_recon_scan(producer, attacker, target, now)
                stats["recon"] += 1
                total_events += 8

            # -------------------------------------------------------------
            # 5. Data Exfiltration Spikes (Periodic massive outbound transfers)
            # -------------------------------------------------------------
            if random.random() < 0.15:  # ~15% chance per second
                exfil_bytes = random.randint(1_500_000, 6_000_000)
                logger.info(f"[{now}] Injecting Data Exfiltration spike ({exfil_bytes / 1e6:.1f} MB)...")
                for _ in range(3):
                    await send_connection(
                        producer,
                        "192.168.1.15",
                        "198.51.100.45",
                        now,
                        orig_bytes=exfil_bytes,
                        resp_bytes=4096,
                    )
                    stats["exfil"] += 1
                    total_events += 1

            # -------------------------------------------------------------
            # 6. Volumetric DDoS Bursts (Bursts of high-rate SYN packets)
            # -------------------------------------------------------------
            if random.random() < 0.08:  # ~8% chance per second
                logger.info(f"[{now}] Injecting Volumetric DDoS burst (30 botnet flows)...")
                target_server = "10.0.0.5"
                for i in range(30):
                    src_bot = f"botnet-{random.randint(1, 150)}.attacker.com"
                    await send_connection(
                        producer,
                        src_bot,
                        target_server,
                        now,
                        dst_port=80,
                        orig_bytes=64,
                        resp_bytes=0,
                        conn_state="S0",
                        history="S",
                    )
                    stats["ddos"] += 1
                    total_events += 1

            # -------------------------------------------------------------
            # Periodic Telemetry Log (Every ~15 seconds)
            # -------------------------------------------------------------
            if time.time() - last_stat_time >= 15.0:
                last_stat_time = time.time()
                elapsed = int(time.time() - start_time)
                rate = total_events / max(1, elapsed)
                logger.info(
                    f"STREAM HEALTH: {total_events} events sent ({rate:.1f} evt/s) | "
                    f"Conn: {stats['connections']} | DNS: {stats['dns']} | TLS: {stats['tls']} | "
                    f"Threats [C2: {stats['c2']}, Exfil: {stats['exfil']}, DDoS: {stats['ddos']}, Recon: {stats['recon']}]"
                )

            # Sleep until next tick, responsive to stop_event
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=tick_interval)
            except asyncio.TimeoutError:
                pass

    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Live generator stopped by user/system.")
    finally:
        if producer:
            await producer.stop()
            logger.info("Kafka producer stopped cleanly. Exited.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Vibhinetra Continuous Live Telemetry Generator")
    parser.add_argument(
        "--loop",
        action="store_true",
        default=os.environ.get("LOOP_FOREVER", "true").lower() in ("true", "1", "yes"),
        help="Run continuously in an infinite loop (default: True)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=int(os.environ.get("DURATION_SECONDS", "0")),
        help="Duration in seconds (0 = run forever, default: 0)",
    )
    parser.add_argument(
        "--tick",
        type=float,
        default=float(os.environ.get("TICK_INTERVAL", "1.0")),
        help="Seconds between ticks (default: 1.0)",
    )
    parser.add_argument(
        "--broker",
        type=str,
        default=os.environ.get("REDPANDA_BROKER", None),
        help="Broker address (default: auto-detected)",
    )

    args = parser.parse_args()

    # If duration > 0, set loop to False unless explicitly forced
    loop_forever = args.loop if args.duration <= 0 else False

    try:
        asyncio.run(
            run_live_demo(
                broker=args.broker,
                duration_seconds=args.duration,
                tick_interval=args.tick,
                loop_forever=loop_forever,
            )
        )
    except KeyboardInterrupt:
        logger.info("Process interrupted by KeyboardInterrupt. Goodbye.")


if __name__ == "__main__":
    main()
