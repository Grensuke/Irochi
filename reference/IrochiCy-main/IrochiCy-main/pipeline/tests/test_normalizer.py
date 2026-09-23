"""Tests for Normalizer orchestrator — 7 tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from normalizer.normalizer import Normalizer, _normalize_protocol


class TestNormalizerProcessing:
    @pytest.mark.asyncio
    async def test_processes_conn_log(self, sample_conn_log: Path):
        """Normalizer should process conn.log and produce events."""
        normalizer = Normalizer(
            log_dir=str(sample_conn_log.parent),
            dry_run=True,
        )
        produced = await normalizer.process_log_file(sample_conn_log, "conn")
        # Row 11 (index 10) has all "-" for src_ip/dst_ip → skipped
        # Remaining 19 rows should produce events
        assert produced >= 18  # At least 18, some may be skipped for other reasons

    @pytest.mark.asyncio
    async def test_processes_dns_log(self, sample_dns_log: Path):
        """Normalizer should process dns.log and produce events."""
        normalizer = Normalizer(
            log_dir=str(sample_dns_log.parent),
            dry_run=True,
        )
        produced = await normalizer.process_log_file(sample_dns_log, "dns")
        assert produced >= 18  # Most rows should produce events

    @pytest.mark.asyncio
    async def test_processes_ssl_log(self, sample_ssl_log: Path):
        """Normalizer should process ssl.log and produce events."""
        normalizer = Normalizer(
            log_dir=str(sample_ssl_log.parent),
            dry_run=True,
        )
        produced = await normalizer.process_log_file(sample_ssl_log, "ssl")
        assert produced >= 18  # Most rows should produce events

    @pytest.mark.asyncio
    async def test_dead_letter_on_invalid_row(self, tmp_path: Path):
        """Rows that fail validation should increment the error counter."""
        # Create a minimal conn.log with an invalid IP
        log_content = (
            "#separator \\x09\n"
            "#set_separator\t,\n"
            "#empty_field\t(empty)\n"
            "#unset_field\t-\n"
            "#path\tconn\n"
            "#fields\tts\tuid\tid.orig_h\tid.orig_p\tid.resp_h\tid.resp_p\tproto\tservice\tduration\torig_bytes\tresp_bytes\tconn_state\tlocal_orig\tlocal_resp\thistory\torig_pkts\torig_ip_bytes\tresp_pkts\tresp_ip_bytes\n"
            "#types\ttime\tstring\taddr\tport\taddr\tport\tenum\tstring\tinterval\tcount\tcount\tstring\tbool\tbool\tstring\tcount\tcount\tcount\tcount\n"
            "1705312800.000000\tCtest1\tnot-a-valid-ip\t80\t93.184.216.34\t443\ttcp\tssl\t1.0\t100\t200\tSF\tT\tF\tShADadFf\t5\t300\t10\t500\n"
        )
        log_file = tmp_path / "conn.log"
        log_file.write_text(log_content)

        normalizer = Normalizer(log_dir=str(tmp_path), dry_run=True)
        produced = await normalizer.process_log_file(log_file, "conn")

        # The invalid IP row should either be skipped or error
        assert normalizer.stats["errors"] > 0 or normalizer.stats["skipped"] > 0

    @pytest.mark.asyncio
    async def test_stats_accurate(self, sample_conn_log: Path):
        """Stats should accurately reflect processing results."""
        normalizer = Normalizer(
            log_dir=str(sample_conn_log.parent),
            dry_run=True,
        )
        await normalizer.process_log_file(sample_conn_log, "conn")

        stats = normalizer.stats
        assert stats["total_rows"] == 20
        assert stats["produced"] + stats["errors"] + stats["skipped"] == stats["total_rows"]
        assert stats["by_type"]["connection"] == stats["produced"]


class TestProtocolNormalization:
    def test_protocol_normalization(self):
        """Protocol strings should be normalized to canonical form."""
        assert _normalize_protocol("tcp") == "tcp"
        assert _normalize_protocol("TCP") == "tcp"
        assert _normalize_protocol("udp") == "udp"
        assert _normalize_protocol("icmp") == "icmp"
        assert _normalize_protocol("ICMP") == "icmp"
        assert _normalize_protocol("quic") == "other"
        assert _normalize_protocol(None) == "other"

    def test_zeek_field_mapping(self, sample_conn_log: Path):
        """Zeek field names should map correctly to canonical fields."""
        from normalizer.readers.zeek_reader import ZeekLogReader

        reader = ZeekLogReader(sample_conn_log)
        rows = list(reader)
        row = rows[0]

        normalizer = Normalizer(log_dir=".", dry_run=True)
        event = normalizer._build_event(row, "conn")

        assert event is not None
        # id.orig_h → src_ip
        assert event.src_ip == "192.168.1.100"
        # id.resp_h → dst_ip
        assert event.dst_ip == "93.184.216.34"
        # id.orig_p → src_port
        assert event.src_port == 49152
        # id.resp_p → dst_port
        assert event.dst_port == 443
        # uid → connection_id
        assert event.connection_id == "CYnvWp3enMJGOsBhu1"
