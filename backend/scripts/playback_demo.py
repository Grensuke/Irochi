import asyncio
import json
import time
import os
from aiokafka import AIOKafkaProducer

TAPE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "real_demo_traffic.jsonl")
EVENTS_PER_SECOND = 50

async def playback_tape():
    print(f"Loading JSONL tape from: {TAPE_FILE}")
    if not os.path.exists(TAPE_FILE):
        print("ERROR: Tape file not found!")
        return

    events = []
    with open(TAPE_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                events.append(line.strip())

    print(f"Loaded {len(events)} events. Starting playback...")
    
    broker = os.environ.get("REDPANDA_BROKER", "localhost:19092")
    producer = AIOKafkaProducer(bootstrap_servers=broker)
    await producer.start()

    try:
        start_time = time.time()
        for i, event_str in enumerate(events):
            # Parse to update ingest timestamp so the backend doesn't flag them as stale
            evt = json.loads(event_str)
            evt["ingest_timestamp"] = int(time.time() * 1000000)
            
            await producer.send_and_wait("vibhinetra.events.connection.v1", json.dumps(evt).encode('utf-8'))
            
            if (i + 1) % 100 == 0:
                print(f"Played {i + 1} / {len(events)} events...")
                
            # Control playback rate
            await asyncio.sleep(1.0 / EVENTS_PER_SECOND)

        end_time = time.time()
        print(f"Playback finished in {end_time - start_time:.2f} seconds.")
    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(playback_tape())
