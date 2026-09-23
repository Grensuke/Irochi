"""Tests for Pydantic canonical event models — 10 tests."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from normalizer.models import SCHEMA_VERSION
from normalizer.models.connection import CanonicalConnectionEvent, ConnectionPayload
from normalizer.models.dns import CanonicalDnsEvent, DnsPayload
from normalizer.models.tls import CanonicalTlsEvent, TlsPayload


def _base_envelope(**overrides):
    """Helper to build a valid envelope dict with overrides."""
    base = {
        "connection_id": "test-uid-001",
        "timestamp": 1705312800000000,
        "sensor_source": "zeek",
        "src_ip": "192.168.1.100",
        "dst_ip": "93.184.216.34",
        "src_port": 49152,
        "dst_port": 443,
        "protocol": "tcp",
    }
    base.update(overrides)
    return base


class TestConnectionEvent:
    def test_connection_event_valid(self):
        """A valid connection event should pass validation."""
        event = CanonicalConnectionEvent(
            payload=ConnectionPayload(
                duration=1.234,
                orig_bytes=1024,
                resp_bytes=8192,
                conn_state="SF",
            ),
            **_base_envelope(),
        )
        assert event.event_type == "connection"
        assert event.payload.duration == 1.234
        assert event.payload.orig_bytes == 1024
        assert event.src_ip == "192.168.1.100"

    def test_connection_event_invalid_ip(self):
        """Invalid IP address should raise ValidationError."""
        with pytest.raises(ValidationError, match="Invalid IP address"):
            CanonicalConnectionEvent(
                payload=ConnectionPayload(),
                **_base_envelope(src_ip="not.an.ip.address"),
            )

    def test_connection_event_port_out_of_range(self):
        """Port outside 0-65535 should raise ValidationError."""
        with pytest.raises(ValidationError, match="Port must be 0-65535"):
            CanonicalConnectionEvent(
                payload=ConnectionPayload(),
                **_base_envelope(src_port=70000),
            )


class TestDnsEvent:
    def test_dns_trailing_dot_stripped(self):
        """Trailing dot on DNS query should be stripped."""
        event = CanonicalDnsEvent(
            payload=DnsPayload(query="google.com.", qtype_name="A"),
            **_base_envelope(protocol="udp"),
        )
        assert event.payload.query == "google.com"

    def test_dns_missing_query_raises(self):
        """Missing required 'query' field should raise ValidationError."""
        with pytest.raises(ValidationError):
            CanonicalDnsEvent(
                payload=DnsPayload(qtype_name="A"),  # type: ignore[call-arg]
                **_base_envelope(protocol="udp"),
            )


class TestTlsEvent:
    def test_tls_all_optional_null(self):
        """TLS event with all optional payload fields as None should be valid."""
        event = CanonicalTlsEvent(
            payload=TlsPayload(),
            **_base_envelope(),
        )
        assert event.event_type == "tls"
        assert event.payload.ja3 is None
        assert event.payload.ja4 is None
        assert event.payload.server_name is None


class TestEnvelopeFields:
    def test_ingest_timestamp_auto_generated(self):
        """ingest_timestamp should be auto-generated."""
        event = CanonicalConnectionEvent(
            payload=ConnectionPayload(),
            **_base_envelope(),
        )
        assert event.ingest_timestamp > 0
        # Should be a reasonable epoch microsecond value (after year 2020)
        assert event.ingest_timestamp > 1577836800000000

    def test_schema_version_is_1_0_0(self):
        """schema_version should default to '1.0.0'."""
        event = CanonicalConnectionEvent(
            payload=ConnectionPayload(),
            **_base_envelope(),
        )
        assert event.schema_version == "1.0.0"
        assert SCHEMA_VERSION == "1.0.0"

    def test_event_id_auto_generated_as_uuid(self):
        """event_id should be auto-generated as a valid UUID."""
        event = CanonicalConnectionEvent(
            payload=ConnectionPayload(),
            **_base_envelope(),
        )
        # Should not raise
        parsed = uuid.UUID(event.event_id)
        assert str(parsed) == event.event_id

    def test_protocol_enum_rejects_unknown(self):
        """Unknown protocol string should raise ValidationError."""
        with pytest.raises(ValidationError):
            CanonicalConnectionEvent(
                payload=ConnectionPayload(),
                **_base_envelope(protocol="quic"),
            )
