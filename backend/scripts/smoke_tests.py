import asyncio
import json
import time
from aiokafka import AIOKafkaProducer

async def send_connection(producer, src, dst, ts, orig_bytes=100, resp_bytes=200):
    event = {
        "event_id": f"evt-{ts}",
        "connection_id": f"conn-{src}-{dst}",
        "timestamp": ts * 1000000,
        "timestamp_precision": "microsecond",
        "ingest_timestamp": int(time.time() * 1000000),
        "sensor_source": "zeek",
        "src_ip": src,
        "dst_ip": dst,
        "src_port": 50000 + (ts % 10000),
        "dst_port": 443,
        "protocol": "tcp",
        "schema_version": "1.0.0",
        "event_type": "connection",
        "payload": {
            "orig_bytes": orig_bytes,
            "resp_bytes": resp_bytes,
            "orig_pkts": 2,
            "resp_pkts": 2,
            "conn_state": "SF",
            "history": "ShADadFf"
        }
    }
    await producer.send_and_wait("vibhinetra.events.connection.v1", json.dumps(event).encode('utf-8'))

async def send_dns(producer, src, query, ts):
    event = {
        "event_id": f"evt-{ts}",
        "connection_id": f"conn-{src}-8.8.8.8",
        "timestamp": ts * 1000000,
        "timestamp_precision": "microsecond",
        "ingest_timestamp": int(time.time() * 1000000),
        "sensor_source": "zeek",
        "src_ip": src,
        "dst_ip": "8.8.8.8",
        "src_port": 50000 + (ts % 10000),
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


async def main():
    producer = AIOKafkaProducer(bootstrap_servers='localhost:19092')
    await producer.start()

    try:
        print("Starting Smoke Tests...")
        base_time = int(time.time()) - 3600

        print("--- DGA Smoke Test ---")
        # 1. Normal domain
        await send_dns(producer, "10.1.1.1", "google.com", base_time)
        # 2. DGA domain
        await send_dns(producer, "10.1.1.2", "xkqzpvwbrytn.com", base_time + 1)
        
        print("--- EXFIL Smoke Test ---")
        # 1. Obvious exfil (High outbound ratio & volume) -> DETECTION
        await send_connection(producer, "10.2.1.1", "192.168.1.100", base_time, orig_bytes=4_000_000, resp_bytes=100_000)
        # 2. Heavy download (Inbound heavy) -> NO THREAT
        await send_connection(producer, "10.2.1.2", "192.168.1.100", base_time, orig_bytes=100_000, resp_bytes=4_000_000)
        # 3. Large balanced (Ratio ~1.0) -> NO THREAT
        await send_connection(producer, "10.2.1.3", "192.168.1.100", base_time, orig_bytes=4_000_000, resp_bytes=4_000_000)

        print("--- C2 Smoke Test ---")
        # Scenario A: Regular beacon (highly regular)
        ts_a = base_time
        for i in range(15):
            await send_connection(producer, "10.3.1.1", "192.168.1.100", ts_a)
            ts_a += 2
        
        # Scenario B: Jittered beacon
        ts_b = base_time
        jitter = [2, 1, 3, 2, 4, 1, 2, 3, 2, 1, 2, 4, 1, 2, 2]
        for i in range(15):
            await send_connection(producer, "10.3.1.2", "192.168.1.100", ts_b)
            ts_b += jitter[i]
            
        # Scenario C: Very short temporal fragment (Only 2 events in window)
        ts_c = base_time
        for i in range(2):
            await send_connection(producer, "10.3.1.3", "192.168.1.100", ts_c)
            ts_c += 2

        print("All events sent. Waiting for processing...")
        await asyncio.sleep(8)
        print("Done.")

    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())
