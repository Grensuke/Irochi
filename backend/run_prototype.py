import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

from app.services.ingest.zeek import ZeekIngestPipeline

logging.basicConfig(level=logging.INFO)

async def main():
    parser = argparse.ArgumentParser(description="Irochi Prototype Ingest Runner")
    parser.add_argument(
        "--pcap",
        type=str,
        default=r"C:\Users\STARK\.gemini\antigravity-ide\brain\bbb22a4a-e551-4ecf-a185-6170a3e90114\scratch\friday_sample.pcap",
        help="Path to the PCAP file to ingest"
    )
    args = parser.parse_args()

    pcap_path = Path(args.pcap).resolve()
    if not pcap_path.is_file():
        logging.error(f"PCAP file not found: {pcap_path}")
        sys.exit(1)

    bpf_filter = ""

    pipeline = ZeekIngestPipeline()
    print(f"Starting prototype ingestion for: {pcap_path}")
    t0 = time.time()
    counts = await pipeline.run_pipeline(str(pcap_path), bpf_filter)
    t1 = time.time()
    print(f"Events produced: {counts}")
    print(f"Processing time: {t1 - t0:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
