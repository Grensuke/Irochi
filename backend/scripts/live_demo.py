import asyncio
import json
import time
import random
from aiokafka import AIOKafkaProducer

async def send_connection(producer, src, dst, ts, orig_bytes=100, resp_bytes=200):
    event = {
        "event_id": f"evt-{ts}-{random.randint(1000, 9999)}",
        "connection_id": f"conn-{src}-{dst}",
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
        "event_type": "connection",
        "payload": {
            "orig_bytes": orig_bytes,
            "resp_bytes": resp_bytes,
            "orig_pkts": max(1, orig_bytes // 1000),
            "resp_pkts": max(1, resp_bytes // 1000),
            "conn_state": "SF",
            "history": "ShADadFf"
        }
    }
    await producer.send_and_wait("vibhinetra.events.connection.v1", json.dumps(event).encode('utf-8'))

async def send_dns(producer, src, query, ts):
    event = {
        "event_id": f"evt-{ts}-{random.randint(1000, 9999)}",
        "connection_id": f"conn-{src}-8.8.8.8",
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
            "qtype_name": "A",
            "rcode_name": "NOERROR",
            "answers": ["192.168.1.1"]
        }
    }
    await producer.send_and_wait("vibhinetra.events.dns.v1", json.dumps(event).encode('utf-8'))

async def run_live_demo():
    print("Starting Live Demo Data Generator for 5 minutes...")
    import os
    broker = os.environ.get("REDPANDA_BROKER", "localhost:19092")
    producer = AIOKafkaProducer(bootstrap_servers=broker)
    await producer.start()

    try:
        start_time = time.time()
        end_time = start_time + 300  # Run for 5 minutes

        while time.time() < end_time:
            now = int(time.time())
            
            # 1. Background Noise (Random normal connections)
            for _ in range(random.randint(2, 5)):
                src = f"192.168.1.{random.randint(10, 50)}"
                dst = f"10.0.0.{random.randint(1, 200)}"
                await send_connection(producer, src, dst, now, orig_bytes=random.randint(100, 5000), resp_bytes=random.randint(100, 50000))
            
            # 2. C2 Beaconing (Every tick from compromised hosts)
            if random.random() < 0.8:
                await send_connection(producer, "192.168.1.15", "198.51.100.45", now, orig_bytes=150, resp_bytes=150)
            if random.random() < 0.6:
                await send_connection(producer, "192.168.1.22", "198.51.100.99", now, orig_bytes=120, resp_bytes=120)

            # 3. DGA / DNS Tunneling
            if random.random() < 0.4:
                dga_domain = f"{''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=12))}.com"
                await send_dns(producer, "192.168.1.15", dga_domain, now)

            # 4. Data Exfiltration (Spikes)
            if random.random() < 0.1:  # 10% chance per second
                print(f"[{now}] Injecting Data Exfiltration spike...")
                for _ in range(3):
                    await send_connection(producer, "192.168.1.15", "198.51.100.45", now, orig_bytes=random.randint(1_000_000, 5_000_000), resp_bytes=50_000)

            # 5. Volumetric DDoS (Bursts)
            if random.random() < 0.05: # 5% chance per second
                print(f"[{now}] Injecting DDoS burst...")
                for _ in range(30):
                    src = f"botnet-{random.randint(1, 100)}.attacker.com"
                    await send_connection(producer, src, "10.0.0.5", now, orig_bytes=64, resp_bytes=0)

            await asyncio.sleep(1.0) # Tick every 1 second

        print("Live Demo Data Generator finished.")
    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(run_live_demo())
