"""CanonicalConnectionEvent — Connection/flow telemetry model.

DIRECTIONAL FIELD RULE (from schema):
  NetFlow IN_PKTS/OUT_PKTS must NOT be auto-mapped to orig_*/resp_*.
  If direction cannot be positively established: set all to None.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from normalizer.models.envelope import CanonicalEnvelope


class ConnectionPayload(BaseModel):
    """Payload fields specific to connection/flow events."""

    duration: Optional[float] = None
    orig_bytes: Optional[int] = None
    resp_bytes: Optional[int] = None
    orig_pkts: Optional[int] = None
    resp_pkts: Optional[int] = None
    conn_state: Optional[str] = None       # Zeek-only (SF, S0, REJ, etc.)
    history: Optional[str] = None           # Zeek-only
    tcp_flags: Optional[int] = None         # NetFlow bitmask
    service: Optional[str] = None           # Zeek-only
    local_orig: Optional[bool] = None       # Zeek-only
    local_resp: Optional[bool] = None       # Zeek-only


class CanonicalConnectionEvent(CanonicalEnvelope):
    """Canonical connection event with connection-specific payload."""

    event_type: Literal["connection"] = "connection"
    payload: ConnectionPayload
