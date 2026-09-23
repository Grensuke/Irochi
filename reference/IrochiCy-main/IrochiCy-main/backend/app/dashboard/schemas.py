"""Dashboard Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class KPIData(BaseModel):
    total_alerts_today: int
    active_threats: int
    events_per_second: float
    detectors_active: int
    pipeline_latency_p95_ms: int
    alerts_delta_today: int


class TimelineBucket(BaseModel):
    timestamp: datetime
    ddos: int = 0
    recon: int = 0
    dns_dga: int = 0
    tls_c2: int = 0
    exfiltration: int = 0


class TimelineResponse(BaseModel):
    buckets: list[TimelineBucket]


class TopThreat(BaseModel):
    threat_type: str
    count: int
    percentage: float


class TopSourceIP(BaseModel):
    ip: str
    event_count: int
    alert_count: int
    last_seen: datetime
    top_threat: Optional[str]


class DashboardSummary(BaseModel):
    kpi: KPIData
    top_threats: list[TopThreat]
    top_source_ips: list[TopSourceIP]
