from enum import Enum
from typing import Optional, List, Union, Literal
from pydantic import BaseModel, Field

class EventType(str, Enum):
    CONNECTION = "connection"
    DNS = "dns"
    TLS = "tls"

class SensorSource(str, Enum):
    ZEEK = "zeek"
    NETFLOW = "netflow"
    IPFIX = "ipfix"
    SFLOW = "sflow"

class Protocol(str, Enum):
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    OTHER = "other"

class TimestampPrecision(str, Enum):
    SECOND = "second"
    MILLISECOND = "millisecond"
    MICROSECOND = "microsecond"
    NANOSECOND = "nanosecond"

class ConnectionPayload(BaseModel):
    duration: Optional[float] = None
    orig_bytes: Optional[int] = None
    resp_bytes: Optional[int] = None
    orig_pkts: Optional[int] = None
    resp_pkts: Optional[int] = None
    conn_state: Optional[str] = None
    history: Optional[str] = None
    tcp_flags: Optional[int] = None
    service: Optional[str] = None
    local_orig: Optional[bool] = None
    local_resp: Optional[bool] = None

class DnsPayload(BaseModel):
    query: str
    qtype_name: str
    qtype: Optional[int] = None
    rcode_name: Optional[str] = None
    rcode: Optional[int] = None
    answers: Optional[List[str]] = None
    rejected: Optional[bool] = None
    trans_id: Optional[int] = None
    rtt: Optional[float] = None

class TlsPayload(BaseModel):
    ja3: Optional[str] = None
    ja3s: Optional[str] = None
    ja4: Optional[str] = None
    ja4s: Optional[str] = None
    server_name: Optional[str] = None
    version: Optional[str] = None
    cipher: Optional[str] = None
    established: Optional[bool] = None
    validation_status: Optional[str] = None
    subject: Optional[str] = None
    issuer: Optional[str] = None

class CanonicalEventEnvelope(BaseModel):
    event_id: str
    connection_id: str
    timestamp: int
    timestamp_precision: TimestampPrecision
    ingest_timestamp: int
    sensor_source: SensorSource
    src_ip: str
    dst_ip: str
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: Protocol
    protocol_number: Optional[int] = None
    schema_version: str

class ConnectionEvent(CanonicalEventEnvelope):
    event_type: Literal[EventType.CONNECTION] = EventType.CONNECTION
    payload: ConnectionPayload

class DnsEvent(CanonicalEventEnvelope):
    event_type: Literal[EventType.DNS] = EventType.DNS
    payload: DnsPayload

class TlsEvent(CanonicalEventEnvelope):
    event_type: Literal[EventType.TLS] = EventType.TLS
    payload: TlsPayload

CanonicalEvent = Union[ConnectionEvent, DnsEvent, TlsEvent]
