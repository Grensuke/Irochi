from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

from app.schemas.features import (
    FeatureRecord,
    EntityType,
    DetectorDomain
)

class DetectorId(str, Enum):
    DDOS = "ddos_detector"
    RECON = "recon_detector"
    DNS_DGA_TUNNEL = "dns_dga_tunnel_detector"
    TLS_C2 = "tls_c2_detector"
    EXFILTRATION = "exfiltration_detector"

class Decision(str, Enum):
    NO_THREAT = "no_threat"
    DETECTION = "detection"
    INSUFFICIENT_DATA = "insufficient_data"
    INVALID_INPUT = "invalid_input"
    DETECTOR_ERROR = "detector_error"

class ThreatType(str, Enum):
    VOLUMETRIC_DDOS = "volumetric_ddos"
    C2_BEACONING = "c2_beaconing"
    DGA_DNS_TUNNEL = "dga_dns_tunnel"
    ENCRYPTED_MALWARE = "encrypted_malware"
    RECON_PORTSCAN = "recon_portscan"
    DATA_EXFILTRATION = "data_exfiltration"

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class SourceFeatureReference(BaseModel):
    feature_id: str
    revision: int

class DetectorInput(BaseModel):
    """
    The exact structured input given to a detector logic evaluation.
    Preserves the complete FeatureRecord unmodified.
    """
    input_id: str
    detector_id: DetectorId
    feature_record: FeatureRecord

class DetectorOutput(BaseModel):
    """
    The final decision from a detector. Not yet an Alert.
    """
    output_id: str
    detector_id: DetectorId
    input_id: str
    entity_type: EntityType
    entity_key: str
    evaluated_at: int  # epoch microseconds
    detector_version: str
    model_version: Optional[str] = None
    decision: Decision
    threat_type: Optional[ThreatType] = None
    confidence: Optional[float] = None
    score: Optional[float] = None
    severity_candidate: Optional[Severity] = None
    evidence: Optional[Dict[str, Any]] = None
    source_feature_references: List[SourceFeatureReference]
    schema_version: str = "1.0"
