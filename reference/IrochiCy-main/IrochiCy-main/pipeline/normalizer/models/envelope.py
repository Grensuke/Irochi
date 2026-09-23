"""CanonicalEnvelope — Base model for all canonical network events.

Matches CANONICAL_EVENT_SCHEMA_FINAL.md exactly.
"""

from __future__ import annotations

import ipaddress
import time
import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

SCHEMA_VERSION = "1.0.0"


class CanonicalEnvelope(BaseModel):
    """Base envelope for all canonical network telemetry events.

    All downstream models (connection, dns, tls) inherit from this.
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: Literal["connection", "dns", "tls"]
    connection_id: str
    timestamp: int  # epoch microseconds (int64)
    timestamp_precision: Literal["microsecond", "millisecond", "second", "unknown"] = "microsecond"
    ingest_timestamp: int = Field(default_factory=lambda: int(time.time() * 1_000_000))
    sensor_source: Literal["zeek", "netflow", "ipfix", "sflow"] = "zeek"
    src_ip: str
    dst_ip: str
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: Literal["tcp", "udp", "icmp", "other"]
    protocol_number: Optional[int] = None
    schema_version: str = SCHEMA_VERSION

    @field_validator("src_ip", "dst_ip")
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        """Validate that the value is a valid IPv4 or IPv6 address."""
        try:
            ipaddress.ip_address(v)
        except ValueError as exc:
            raise ValueError(f"Invalid IP address: {v!r}") from exc
        return v

    @field_validator("src_port", "dst_port")
    @classmethod
    def validate_port_range(cls, v: Optional[int]) -> Optional[int]:
        """Validate port is in range 0-65535."""
        if v is not None and (v < 0 or v > 65535):
            raise ValueError(f"Port must be 0-65535, got {v}")
        return v
