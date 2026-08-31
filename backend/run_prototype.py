import asyncio
import logging
from app.services.ingest.zeek import ZeekIngestPipeline

logging.basicConfig(level=logging.INFO)

async def main():
    import time
    pcap = r"C:\Users\STARK\.gemini\antigravity-ide\brain\bbb22a4a-e551-4ecf-a185-6170a3e90114\scratch\friday_sample.pcap"
    bpf_filter = ""

    pipeline = ZeekIngestPipeline()
    print("Starting prototype ingestion...")
    t0 = time.time()
    counts = await pipeline.run_pipeline(pcap, bpf_filter)
    t1 = time.time()
    print(f"Events produced: {counts}")
    print(f"Processing time: {t1 - t0:.2f} seconds")
    print(f"Events produced: {counts}")

if __name__ == "__main__":
    asyncio.run(main())
