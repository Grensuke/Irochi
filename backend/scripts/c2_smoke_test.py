import asyncio
import json
import time
from aiokafka import AIOKafkaProducer

async def send_event(producer, src, dst, ts, port=443):
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
        "dst_port": port,
        "protocol": "tcp",
        "schema_version": "1.0.0",
        "event_type": "connection",
        "payload": {
            "orig_bytes": 100,
            "resp_bytes": 200,
            "orig_pkts": 2,
            "resp_pkts": 2,
            "conn_state": "SF",
            "history": "ShADadFf"
        }
    }
    await producer.send_and_wait("irochi.events.connection.v1", json.dumps(event).encode('utf-8'))

async def main():
    producer = AIOKafkaProducer(bootstrap_servers='localhost:19092')
    await producer.start()

    try:
        print("Starting C2 Smoke Tests...")
        base_time = int(time.time()) - 3600

        # Scenario A: Regular beacon (highly regular, variance ~ 0, every 10s)
        # 15 connections -> freq = 15/window. window is 60s for tumbling? Wait, window_size_sec is 60 usually.
        # Let's check mechanism window size. Usually 60s.
        print("Scenario A: Regular Beacon (10.0.0.1 -> 192.168.1.100)")
        ts_a = base_time
        for i in range(15):
            await send_event(producer, "10.0.0.1", "192.168.1.100", ts_a)
            ts_a += 2  # exactly 2 seconds apart, very regular

        # Scenario B: Jittered beacon (same freq, but jittered)
        print("Scenario B: Jittered Beacon (10.0.0.2 -> 192.168.1.100)")
        ts_b = base_time
        jitter = [2, 1, 3, 2, 4, 1, 2, 3, 2, 1, 2, 4, 1, 2, 2]
        for i in range(15):
            await send_event(producer, "10.0.0.2", "192.168.1.100", ts_b)
            ts_b += jitter[i]

        # Scenario C: High-frequency irregular traffic
        print("Scenario C: High-frequency Irregular (10.0.0.3 -> 192.168.1.100)")
        ts_c = base_time
        irregular = [1, 10, 1, 1, 20, 2, 5, 1, 1, 15, 2, 1, 1, 1, 30]
        for i in range(15):
            await send_event(producer, "10.0.0.3", "192.168.1.100", ts_c)
            ts_c += irregular[i]
        
        print("All events sent. Waiting for processing...")
        await asyncio.sleep(5)
        print("Done.")

    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())
