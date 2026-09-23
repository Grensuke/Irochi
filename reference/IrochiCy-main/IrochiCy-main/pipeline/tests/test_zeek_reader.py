"""Tests for ZeekLogReader — 10 tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from normalizer.readers.zeek_reader import ZeekLogReader


class TestConnLogReader:
    def test_reader_parses_conn_header(self, sample_conn_log: Path):
        """Reader should parse header and extract correct field names."""
        reader = ZeekLogReader(sample_conn_log)
        assert "ts" in reader.fields
        assert "uid" in reader.fields
        assert "id.orig_h" in reader.fields
        assert "id.resp_h" in reader.fields
        assert "proto" in reader.fields
        assert reader.log_path == "conn"

    def test_reader_iterates_20_conn_rows(self, sample_conn_log: Path):
        """Reader should iterate over all 20 data rows in conn.log."""
        reader = ZeekLogReader(sample_conn_log)
        rows = list(reader)
        assert len(rows) == 20

    def test_reader_unset_field_becomes_none(self, sample_conn_log: Path):
        """Unset fields ('-') should become None."""
        reader = ZeekLogReader(sample_conn_log)
        rows = list(reader)
        # Row 5 (index 4) has S0 state with duration="-"
        s0_row = rows[4]
        assert s0_row["duration"] is None
        assert s0_row["service"] is None

    def test_reader_timestamp_to_microseconds(self, sample_conn_log: Path):
        """Timestamp should be converted to epoch microseconds (int)."""
        reader = ZeekLogReader(sample_conn_log)
        rows = list(reader)
        ts = rows[0]["ts"]
        assert isinstance(ts, int)
        # 1705312800.000000 → 1705312800000000
        assert ts == 1705312800000000

    def test_reader_port_to_int(self, sample_conn_log: Path):
        """Port fields should be converted to int."""
        reader = ZeekLogReader(sample_conn_log)
        rows = list(reader)
        assert isinstance(rows[0]["id.orig_p"], int)
        assert rows[0]["id.orig_p"] == 49152
        assert isinstance(rows[0]["id.resp_p"], int)
        assert rows[0]["id.resp_p"] == 443

    def test_reader_bool_fields(self, sample_conn_log: Path):
        """Bool fields should be converted: 'T'→True, 'F'→False."""
        reader = ZeekLogReader(sample_conn_log)
        rows = list(reader)
        assert rows[0]["local_orig"] is True
        assert rows[0]["local_resp"] is False


class TestDnsLogReader:
    def test_reader_dns_log_20_rows(self, sample_dns_log: Path):
        """Reader should iterate over all 20 data rows in dns.log."""
        reader = ZeekLogReader(sample_dns_log)
        rows = list(reader)
        assert len(rows) == 20

    def test_reader_set_field_to_list(self, sample_dns_log: Path):
        """Set fields should be split into a list."""
        reader = ZeekLogReader(sample_dns_log)
        rows = list(reader)
        # Row 8 (index 7): answers = "104.16.85.20,104.16.86.20"
        answers = rows[7]["answers"]
        assert isinstance(answers, list)
        assert len(answers) == 2
        assert "104.16.85.20" in answers


class TestSslLogReader:
    def test_reader_ssl_log_20_rows(self, sample_ssl_log: Path):
        """Reader should iterate over all 20 data rows in ssl.log."""
        reader = ZeekLogReader(sample_ssl_log)
        rows = list(reader)
        assert len(rows) == 20

    def test_reader_missing_ja4_column_yields_none_not_crash(self, sample_ssl_log: Path):
        """If ja4/ja4s columns are absent, reader should NOT crash.

        The sample_ssl.log fixture deliberately omits ja4/ja4s columns
        to simulate a Zeek installation without the JA4 package.
        """
        reader = ZeekLogReader(sample_ssl_log)
        assert "ja4" not in reader.fields
        assert "ja4s" not in reader.fields
        # Reader should still iterate fine
        rows = list(reader)
        assert len(rows) == 20
        # Rows should not have ja4 key at all (silently absent)
        assert "ja4" not in rows[0]
