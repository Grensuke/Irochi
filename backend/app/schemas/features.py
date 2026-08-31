from enum import Enum
from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field

class FeatureMechanism(str, Enum):
    ENRICHMENT = "enrichment"
    WINDOWED = "windowed"
    CORRELATION = "correlation"

class DetectorDomain(str, Enum):
    DDOS = "ddos"
    RECON = "recon"
    DNS = "dns"
    TLS_C2 = "tls_c2"
    EXFIL = "exfil"

class EntityType(str, Enum):
    SOURCE = "source"
    DESTINATION = "destination"
    PAIR = "pair"
    CONNECTION = "connection"

class WindowType(str, Enum):
    TUMBLING = "tumbling"
    SLIDING = "sliding"
    SESSION = "session"

class CorrelationStatus(str, Enum):
    PARTIAL = "partial"
    COMPLETE = "complete"
    LATE_AMENDMENT = "late_amendment"

class FeatureRecordEnvelope(BaseModel):
    feature_id: str
    mechanism: FeatureMechanism
    detector_domain: DetectorDomain
    entity_type: EntityType
    entity_key: str
    window_type: Optional[WindowType] = None
    window_start: Optional[int] = None
    window_end: Optional[int] = None
    computed_at: int
    schema_version: str
    revision: int
    provenance: Optional[Dict[str, Any]] = None

class DdosFeaturePayload(BaseModel):
    packet_rate: Optional[float] = None
    byte_rate: Optional[float] = None
    syn_ratio: Optional[float] = None
    source_ip_entropy: Optional[float] = None

class ReconFeaturePayload(BaseModel):
    unique_destination_ports: Optional[int] = None
    unique_destination_hosts: Optional[int] = None
    connection_fan_out: Optional[int] = None
    scan_rate: Optional[float] = None

class DnsFeaturePayload(BaseModel):
    # Enrichment
    domain_entropy: Optional[float] = None
    query_length: Optional[int] = None
    n_gram_score: Optional[float] = None
    label_count: Optional[int] = None
    max_label_length: Optional[int] = None
    # Windowed
    query_frequency: Optional[float] = None
    record_type_distribution: Optional[Dict[str, float]] = None

class TlsC2FeaturePayload(BaseModel):
    # Enrichment
    ja3_blacklist_match: Optional[bool] = None
    # Windowed
    inter_arrival_time: Optional[float] = None
    beacon_periodicity: Optional[float] = None
    periodicity_variance: Optional[float] = None
    regularity: Optional[float] = None
    connection_frequency: Optional[float] = None
    # Correlation
    correlation_status: Optional[CorrelationStatus] = None

class ExfilFeaturePayload(BaseModel):
    outbound_inbound_ratio: Optional[float] = None
    byte_rate: Optional[float] = None

class DdosFeatureRecord(FeatureRecordEnvelope):
    detector_domain: Literal[DetectorDomain.DDOS] = DetectorDomain.DDOS
    payload: DdosFeaturePayload

class ReconFeatureRecord(FeatureRecordEnvelope):
    detector_domain: Literal[DetectorDomain.RECON] = DetectorDomain.RECON
    payload: ReconFeaturePayload

class DnsFeatureRecord(FeatureRecordEnvelope):
    detector_domain: Literal[DetectorDomain.DNS] = DetectorDomain.DNS
    payload: DnsFeaturePayload

class TlsC2FeatureRecord(FeatureRecordEnvelope):
    detector_domain: Literal[DetectorDomain.TLS_C2] = DetectorDomain.TLS_C2
    payload: TlsC2FeaturePayload

class ExfilFeatureRecord(FeatureRecordEnvelope):
    detector_domain: Literal[DetectorDomain.EXFIL] = DetectorDomain.EXFIL
    payload: ExfilFeaturePayload

FeatureRecord = Union[
    DdosFeatureRecord,
    ReconFeatureRecord,
    DnsFeatureRecord,
    TlsC2FeatureRecord,
    ExfilFeatureRecord
]
