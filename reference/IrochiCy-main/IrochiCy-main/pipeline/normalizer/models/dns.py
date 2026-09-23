"""CanonicalDnsEvent — DNS query/response telemetry model."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, field_validator

from normalizer.models.envelope import CanonicalEnvelope


class DnsPayload(BaseModel):
    """Payload fields specific to DNS events."""

    query: str                              # REQUIRED — trailing dot stripped
    qtype_name: str                         # REQUIRED (A, AAAA, TXT, MX, etc.)
    qtype: Optional[int] = None
    rcode_name: Optional[str] = None
    rcode: Optional[int] = None
    answers: Optional[list[str]] = None
    rejected: Optional[bool] = None
    trans_id: Optional[int] = None
    rtt: Optional[float] = None

    @field_validator("query")
    @classmethod
    def strip_trailing_dot(cls, v: str) -> str:
        """Strip trailing dot from DNS query (e.g. 'google.com.' → 'google.com')."""
        return v.rstrip(".")


class CanonicalDnsEvent(CanonicalEnvelope):
    """Canonical DNS event with DNS-specific payload."""

    event_type: Literal["dns"] = "dns"
    payload: DnsPayload
