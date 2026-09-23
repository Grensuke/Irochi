"""Canonical event model exports."""

from __future__ import annotations

from typing import Union

from normalizer.models.connection import CanonicalConnectionEvent, ConnectionPayload
from normalizer.models.dns import CanonicalDnsEvent, DnsPayload
from normalizer.models.envelope import CanonicalEnvelope, SCHEMA_VERSION
from normalizer.models.tls import CanonicalTlsEvent, TlsPayload

CanonicalEvent = Union[CanonicalConnectionEvent, CanonicalDnsEvent, CanonicalTlsEvent]

__all__ = [
    "SCHEMA_VERSION",
    "CanonicalEnvelope",
    "CanonicalEvent",
    "CanonicalConnectionEvent",
    "ConnectionPayload",
    "CanonicalDnsEvent",
    "DnsPayload",
    "CanonicalTlsEvent",
    "TlsPayload",
]
