"""CanonicalTlsEvent — TLS/SSL handshake telemetry model."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from normalizer.models.envelope import CanonicalEnvelope


class TlsPayload(BaseModel):
    """Payload fields specific to TLS/SSL events. All fields optional."""

    ja3: Optional[str] = None
    ja3s: Optional[str] = None
    ja4: Optional[str] = None
    ja4s: Optional[str] = None
    server_name: Optional[str] = None       # SNI
    version: Optional[str] = None
    cipher: Optional[str] = None
    established: Optional[bool] = None
    validation_status: Optional[str] = None
    subject: Optional[str] = None
    issuer: Optional[str] = None


class CanonicalTlsEvent(CanonicalEnvelope):
    """Canonical TLS event with TLS-specific payload."""

    event_type: Literal["tls"] = "tls"
    payload: TlsPayload
