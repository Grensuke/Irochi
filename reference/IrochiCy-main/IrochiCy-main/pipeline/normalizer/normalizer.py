"""Normalizer — Orchestrator for reading Zeek logs and producing canonical events.

Two modes:
  batch: Process all log files in a directory once, then exit.
  watch: Tail log files continuously as Zeek writes them (live mode).
  csv-batch: Process CICFlowMeter CSV files instead of Zeek logs.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Optional

import structlog
from pydantic import ValidationError

from normalizer.config import settings
from normalizer.models import CanonicalEvent
from normalizer.models.connection import CanonicalConnectionEvent, ConnectionPayload
from normalizer.models.dns import CanonicalDnsEvent, DnsPayload
from normalizer.models.tls import CanonicalTlsEvent, TlsPayload
from normalizer.producer import NormalizerProducer
from normalizer.readers.zeek_reader import ZeekLogReader
from normalizer.readers.cic_csv_reader import CicCsvReader

logger = structlog.get_logger(__name__)

# Zeek log type → canonical event type
LOG_TYPE_MAP = {
    "conn": "connection",
    "dns": "dns",
    "ssl": "tls",
}

# Zeek protocol → canonical protocol
PROTOCOL_MAP = {
    "tcp": "tcp",
    "udp": "udp",
    "icmp": "icmp",
}


def _normalize_protocol(proto: Optional[str]) -> str:
    """Normalize a protocol string to canonical form."""
    if proto is None:
        return "other"
    return PROTOCOL_MAP.get(proto.lower(), "other")


class Normalizer:
    """Orchestrates reading Zeek logs and producing canonical events.

    Args:
        log_dir: Path to directory containing Zeek log files.
        brokers: Redpanda/Kafka broker address.
        dry_run: If True, skip producing to Redpanda (stats only).
    """

    def __init__(
        self,
        log_dir: str,
        brokers: str = "localhost:9092",
        dry_run: bool = False,
    ) -> None:
        self.log_dir = Path(log_dir)
        self.brokers = brokers
        self.dry_run = dry_run
        self._producer: Optional[NormalizerProducer] = None
        self._stats = {
            "total_rows": 0,
            "produced": 0,
            "errors": 0,
            "skipped": 0,
            "by_type": {"connection": 0, "dns": 0, "tls": 0},
        }
        # For watch mode: track last-read file position per log file
        self._file_positions: dict[str, int] = {}

    def _build_event(self, row: dict, log_type: str) -> Optional[CanonicalEvent]:
        """Build a CanonicalEvent from a parsed Zeek row.

        Args:
            row: Parsed dict from ZeekLogReader.
            log_type: One of "conn", "dns", "ssl".

        Returns:
            CanonicalEvent or None if row is missing critical fields.
        """
        src_ip = row.get("id.orig_h")
        dst_ip = row.get("id.resp_h")
        if not src_ip or not dst_ip:
            return None

        protocol = _normalize_protocol(row.get("proto"))
        timestamp = row.get("ts")
        if timestamp is None:
            return None

        # Common envelope fields
        envelope = {
            "connection_id": row.get("uid", ""),
            "timestamp": timestamp,
            "timestamp_precision": "microsecond",
            "sensor_source": "zeek",
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": row.get("id.orig_p"),
            "dst_port": row.get("id.resp_p"),
            "protocol": protocol,
        }

        event_type = LOG_TYPE_MAP.get(log_type)

        if event_type == "connection":
            payload = ConnectionPayload(
                duration=row.get("duration"),
                orig_bytes=row.get("orig_bytes"),
                resp_bytes=row.get("resp_bytes"),
                orig_pkts=row.get("orig_pkts"),
                resp_pkts=row.get("resp_pkts"),
                conn_state=row.get("conn_state"),
                history=row.get("history"),
                service=row.get("service"),
                local_orig=row.get("local_orig"),
                local_resp=row.get("local_resp"),
            )
            return CanonicalConnectionEvent(payload=payload, **envelope)

        elif event_type == "dns":
            query = row.get("query")
            qtype_name = row.get("qtype_name")
            if not query or not qtype_name:
                return None
            payload = DnsPayload(
                query=query,
                qtype_name=qtype_name,
                qtype=row.get("qtype"),
                rcode_name=row.get("rcode_name"),
                rcode=row.get("rcode"),
                answers=row.get("answers"),
                rejected=row.get("rejected"),
                trans_id=row.get("trans_id"),
                rtt=row.get("rtt"),
            )
            return CanonicalDnsEvent(payload=payload, **envelope)

        elif event_type == "tls":
            payload = TlsPayload(
                ja3=row.get("ja3"),
                ja3s=row.get("ja3s"),
                ja4=row.get("ja4"),
                ja4s=row.get("ja4s"),
                server_name=row.get("server_name"),
                version=row.get("version"),
                cipher=row.get("cipher"),
                established=row.get("established"),
                validation_status=row.get("validation_status"),
                subject=row.get("subject"),
                issuer=row.get("issuer"),
            )
            return CanonicalTlsEvent(payload=payload, **envelope)

        return None

    async def process_log_file(self, log_path: Path, log_type: str) -> int:
        """Process a single Zeek log file.

        Args:
            log_path: Path to the log file.
            log_type: One of "conn", "dns", "ssl".

        Returns:
            Number of events produced.
        """
        if not log_path.exists():
            logger.warning("log_file_not_found", path=str(log_path))
            return 0

        reader = ZeekLogReader(log_path)
        produced = 0
        event_type = LOG_TYPE_MAP.get(log_type, log_type)

        for row in reader:
            self._stats["total_rows"] += 1
            try:
                event = self._build_event(row, log_type)
                if event is None:
                    self._stats["skipped"] += 1
                    continue

                if not self.dry_run and self._producer:
                    await self._producer.produce_event(event)

                self._stats["produced"] += 1
                self._stats["by_type"][event_type] += 1
                produced += 1

            except ValidationError as exc:
                self._stats["errors"] += 1
                logger.warning(
                    "validation_error",
                    log_type=log_type,
                    error=str(exc),
                )
                if not self.dry_run and self._producer:
                    await self._producer.produce_dead_letter(row, str(exc))

            except Exception as exc:
                self._stats["errors"] += 1
                logger.error(
                    "processing_error",
                    log_type=log_type,
                    error=str(exc),
                )

        logger.info(
            "log_file_processed",
            path=str(log_path),
            log_type=log_type,
            produced=produced,
        )
        return produced

    async def run_directory(self) -> dict:
        """Process conn.log, dns.log, ssl.log in the log directory.

        Returns:
            Stats dict with processing results.
        """
        start_time = time.time()

        if not self.dry_run:
            self._producer = NormalizerProducer(self.brokers)
            await self._producer.start()

        try:
            # Process in order: conn, dns, ssl
            for log_file, log_type in [
                ("conn.log", "conn"),
                ("dns.log", "dns"),
                ("ssl.log", "ssl"),
            ]:
                log_path = self.log_dir / log_file
                if log_path.exists():
                    await self.process_log_file(log_path, log_type)
                else:
                    logger.info("log_file_missing", path=str(log_path))

        finally:
            if self._producer:
                await self._producer.stop()

        elapsed = time.time() - start_time
        self._stats["elapsed_seconds"] = round(elapsed, 2)
        self._stats["events_per_second"] = round(
            self._stats["produced"] / elapsed if elapsed > 0 else 0, 2
        )

        logger.info("directory_processing_complete", stats=self._stats)

        # Publish stats to Redis if available
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.redis_url)
            await r.set("pipeline:events_per_second", str(self._stats["events_per_second"]))
            await r.set("pipeline:normalizer:stats", json.dumps(self._stats))
            await r.aclose()
        except Exception:
            logger.debug("redis_stats_publish_skipped")

        return self._stats

    async def run_watch(self) -> None:
        """Watch log directory for new lines (live mode).

        Polls every watch_poll_interval seconds for new data in
        conn.log, dns.log, ssl.log.
        """
        if not self.dry_run:
            self._producer = NormalizerProducer(self.brokers)
            await self._producer.start()

        log_files = {
            "conn.log": "conn",
            "dns.log": "dns",
            "ssl.log": "ssl",
        }

        logger.info("watch_mode_started", log_dir=str(self.log_dir))

        try:
            while True:
                for log_file, log_type in log_files.items():
                    log_path = self.log_dir / log_file
                    if not log_path.exists():
                        continue

                    file_key = str(log_path)
                    current_size = log_path.stat().st_size
                    last_pos = self._file_positions.get(file_key, 0)

                    if current_size <= last_pos:
                        continue

                    # Read new lines
                    with open(log_path, "r", encoding="utf-8") as fh:
                        fh.seek(last_pos)
                        new_content = fh.read()
                        self._file_positions[file_key] = fh.tell()

                    # Parse new lines using a temporary reader approach
                    for line in new_content.strip().split("\n"):
                        if line.startswith("#") or not line.strip():
                            continue

                        # We need field names from the reader
                        reader = ZeekLogReader(log_path)
                        parts = line.split(reader.separator)
                        if len(parts) != len(reader.fields):
                            continue

                        row = {}
                        for i, (field, raw_val) in enumerate(zip(reader.fields, parts)):
                            type_hint = reader.types[i] if i < len(reader.types) else "string"
                            row[field] = reader._coerce_value(raw_val, type_hint)

                        try:
                            event = self._build_event(row, log_type)
                            if event and not self.dry_run and self._producer:
                                await self._producer.produce_event(event)
                                self._stats["produced"] += 1
                                event_type = LOG_TYPE_MAP.get(log_type, log_type)
                                self._stats["by_type"][event_type] += 1
                        except Exception as exc:
                            self._stats["errors"] += 1
                            logger.warning("watch_processing_error", error=str(exc))

                await asyncio.sleep(settings.watch_poll_interval)

        except KeyboardInterrupt:
            logger.info("watch_mode_stopped")
        finally:
            if self._producer:
                await self._producer.stop()

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    async def run_csv_batch(self, csv_dir: Path) -> dict:
        """Process all CSV files in the given directory using CicCsvReader."""
        start_time = time.time()
        
        if not self.dry_run:
            self._producer = NormalizerProducer(self.brokers)
            await self._producer.start()

        try:
            if not csv_dir.exists():
                logger.error("csv_dir_not_found", path=str(csv_dir))
                return self._stats

            for csv_file in csv_dir.glob("*.csv"):
                logger.info("processing_csv", file=str(csv_file))
                reader = CicCsvReader(csv_file)
                
                async for event in reader.read_events():
                    self._stats["total_rows"] += 1
                    try:
                        if not self.dry_run and self._producer:
                            await self._producer.produce_event(event)
                            
                        self._stats["produced"] += 1
                        self._stats["by_type"]["connection"] += 1
                    except Exception as exc:
                        self._stats["errors"] += 1
                        logger.error("csv_processing_error", error=str(exc))
        finally:
            if self._producer:
                await self._producer.stop()

        elapsed = time.time() - start_time
        self._stats["elapsed_seconds"] = round(elapsed, 2)
        self._stats["events_per_second"] = round(
            self._stats["produced"] / elapsed if elapsed > 0 else 0, 2
        )

        logger.info("csv_batch_complete", stats=self._stats)
        return self._stats


def main() -> None:
    """CLI entrypoint for the normalizer."""
    parser = argparse.ArgumentParser(
        description="SIH26145 Pipeline Normalizer — Zeek log → Canonical events → Redpanda"
    )
    parser.add_argument(
        "--log-dir",
        required=True,
        help="Path to directory containing Zeek log files",
    )
    parser.add_argument(
        "--brokers",
        default="localhost:9092",
        help="Redpanda/Kafka broker address (default: localhost:9092)",
    )
    parser.add_argument(
        "--mode",
        choices=["batch", "watch", "csv-batch"],
        default="batch",
        help="Processing mode: batch, watch, or csv-batch",
    )
    parser.add_argument(
        "--csv-dir",
        help="Path to directory containing MachineLearningCVE CSV files (required for csv-batch mode)",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Dry run — parse and validate but do not produce to Redpanda",
    )
    args = parser.parse_args()

    normalizer = Normalizer(
        log_dir=args.log_dir,
        brokers=args.brokers,
        dry_run=args.stats_only,
    )

    if args.mode == "batch":
        stats = asyncio.run(normalizer.run_directory())
        print(json.dumps(stats, indent=2))
    elif args.mode == "csv-batch":
        if not args.csv_dir:
            parser.error("--csv-dir is required when --mode is csv-batch")
        stats = asyncio.run(normalizer.run_csv_batch(Path(args.csv_dir)))
        print(json.dumps(stats, indent=2))
    else:
        asyncio.run(normalizer.run_watch())


if __name__ == "__main__":
    main()
