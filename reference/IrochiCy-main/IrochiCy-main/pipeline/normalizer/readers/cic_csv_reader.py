"""CICFlowMeter CSV Reader.

Reads MachineLearningCVE CSV files (CIC-IDS-2017) and maps flow statistics
to CanonicalConnectionEvent. Mocks missing fields like IPs and timestamps.
"""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

import structlog

from normalizer.models.connection import CanonicalConnectionEvent, ConnectionPayload

logger = structlog.get_logger(__name__)


class CicCsvReader:
    """Reads CICFlowMeter CSV files and yields CanonicalConnectionEvent objects."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        # We need a fake start time to simulate timestamps
        self.current_time_us = int(time.time() * 1_000_000)

    async def read_events(self) -> AsyncIterator[CanonicalConnectionEvent]:
        """Read the CSV and yield canonical connection events."""
        logger.info("reading_cic_csv", file=str(self.file_path))

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                # Strip spaces from fieldnames
                if reader.fieldnames:
                    reader.fieldnames = [name.strip() for name in reader.fieldnames]

                for row in reader:
                    event = self._parse_row(row)
                    if event:
                        yield event

        except Exception as exc:
            logger.error("csv_read_failed", file=str(self.file_path), error=str(exc))

    def _parse_row(self, row: dict) -> CanonicalConnectionEvent | None:
        """Parse a single CSV row into a CanonicalConnectionEvent."""
        try:
            # Extract basic flow features
            dst_port_str = row.get("Destination Port", "0")
            dst_port = int(dst_port_str) if dst_port_str.isdigit() else 0

            # Flow Duration is in microseconds
            duration_us_str = row.get("Flow Duration", "0")
            duration_us = float(duration_us_str) if duration_us_str.replace('.', '', 1).isdigit() else 0.0
            duration_sec = duration_us / 1_000_000.0

            # Packets and Bytes
            fwd_pkts = int(row.get("Total Fwd Packets", "0"))
            bwd_pkts = int(row.get("Total Backward Packets", "0"))
            fwd_bytes = int(row.get("Total Length of Fwd Packets", "0"))
            bwd_bytes = int(row.get("Total Length of Bwd Packets", "0"))

            # Create mock IPs. We can use slightly varying IPs so Recon detector doesn't completely break,
            # but it won't be accurate.
            # Using random-ish IPs based on port to give some variation
            mock_src_ip = f"192.168.1.{100 + (dst_port % 100)}"
            mock_dst_ip = f"10.0.0.{1 + (dst_port % 50)}"

            # Advance the fake timestamp by duration
            self.current_time_us += int(duration_us) if duration_us > 0 else 1000

            payload = ConnectionPayload(
                duration=duration_sec,
                orig_bytes=fwd_bytes,
                resp_bytes=bwd_bytes,
                orig_pkts=fwd_pkts,
                resp_pkts=bwd_pkts,
                conn_state="SF",  # Mock state
                protocol="tcp",   # Mock protocol
            )

            event = CanonicalConnectionEvent(
                connection_id=uuid4().hex,
                timestamp=self.current_time_us,
                sensor_source="cicflowmeter",
                src_ip=mock_src_ip,
                dst_ip=mock_dst_ip,
                src_port=49152,  # Mock ephemeral port
                dst_port=dst_port,
                protocol="tcp",
                payload=payload,
            )
            return event
        except Exception as exc:
            logger.debug("csv_row_parse_failed", error=str(exc))
            return None
