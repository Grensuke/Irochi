import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.incident import Incident
from app.models.alert import Alert
from app.services.postgres_incident_service import PostgresIncidentService

# OPEN / UNVALIDATED — tune during evaluation
BASE_WEIGHT = {
    "recon_portscan": 15,
    "dga_dns_tunnel": 20,
    "c2_beaconing": 22,
    "encrypted_malware": 20,
    "data_exfiltration": 25,
    "volumetric_ddos": 18,
    "unknown_threat": 12,
}
ESCALATION_CONSTANT = 0.15

KILL_CHAIN_ORDER = [
    "recon_portscan", 
    "dga_dns_tunnel", 
    "c2_beaconing", 
    "encrypted_malware", 
    "data_exfiltration"
]

KILL_CHAIN_NEXT = {
    "recon_portscan": "dga_dns_tunnel",
    "dga_dns_tunnel": "c2_beaconing",
    "c2_beaconing": "encrypted_malware",
    "encrypted_malware": "data_exfiltration",
    "data_exfiltration": None,
}

FORECAST_NOTE = "This is a risk forecast based on observed kill-chain progression, not a claim that the next stage has occurred."


class IncidentEngine:
    async def on_alert(self, alert_payload: dict[str, Any], session: AsyncSession) -> Incident:
        incident_service = PostgresIncidentService(session)
        
        # 1. find-or-open incident by src_ip within the 60-min window
        src_ip = alert_payload.get("src_ip")
        if not src_ip:
            # If no source IP, we can't reliably cluster it currently
            # Returning None or just creating a standalone incident? 
            # The brief says "Correlate by the alert's derived src_ip". 
            # If there's no src_ip, we skip incident correlation for now.
            return None

        alert_time_str = alert_payload["timestamp"]
        try:
            alert_time = datetime.fromisoformat(alert_time_str.replace("Z", "+00:00"))
        except ValueError:
            alert_time = datetime.now(timezone.utc)
            
        window_start = alert_time - timedelta(minutes=60)
        
        incident = await incident_service.get_open_incident_for_src_ip(src_ip, window_start)
        
        if not incident:
            incident = Incident(
                entity_type="source",
                entity_key=src_ip,
                status="open",
                opened_at=alert_time,
                updated_at=alert_time,
                last_event_at=alert_time,
                member_alert_ids=[],
                distinct_threat_types=[],
                risk_score=0.0,
                risk_breakdown={},
                stage_state="anomaly",
            )
            incident = await incident_service.create_incident(incident)

        # 2. attach this alert_id to member_alert_ids, refresh last_event_at
        alert_id = alert_payload["alert_id"]
        member_alert_ids = incident.member_alert_ids.copy()
        if alert_id not in member_alert_ids:
            member_alert_ids.append(alert_id)
            
        last_event_at = max(incident.last_event_at, alert_time)
        updated_at = datetime.now(timezone.utc)

        # Write incident_id back onto the Alert row
        stmt = select(Alert).where(Alert.alert_id == uuid.UUID(alert_id))
        result = await session.execute(stmt)
        alert_row = result.scalar_one_or_none()
        if alert_row:
            alert_row.incident_id = incident.incident_id
            await session.commit()

        # 3. fetch all currently open member alerts for this incident from Postgres
        # Since we just updated the Alert, we can fetch all of them.
        stmt = select(Alert).where(Alert.incident_id == incident.incident_id)
        result = await session.execute(stmt)
        member_alerts = result.scalars().all()

        # 4. recompute risk_score / risk_breakdown
        # Group alerts by threat_type to find max confidence
        max_confidence_by_threat = {}
        for a in member_alerts:
            tt = a.threat_type
            conf = a.confidence if a.confidence is not None else 1.0
            if tt not in max_confidence_by_threat or conf > max_confidence_by_threat[tt]:
                max_confidence_by_threat[tt] = conf

        risk_breakdown = {}
        for tt, max_conf in max_confidence_by_threat.items():
            base_wt = BASE_WEIGHT.get(tt, 10)  # default weight if unknown
            risk_breakdown[tt] = base_wt * max_conf
            
        raw_score = sum(risk_breakdown.values())
        distinct_types = len(risk_breakdown)
        escalation = 1.0 + ESCALATION_CONSTANT * max(0, distinct_types - 1)
        risk_score = min(100.0, round(raw_score * escalation))
        distinct_threat_types = list(risk_breakdown.keys())

        # stage_state / current_stage
        kill_chain_types_present = [tt for tt in distinct_threat_types if tt in KILL_CHAIN_ORDER]
        kill_chain_count = len(kill_chain_types_present)
        
        has_exfil = "data_exfiltration" in distinct_threat_types
        has_ddos = "volumetric_ddos" in distinct_threat_types
        has_anomaly = "unknown_threat" in distinct_threat_types

        # Determine stage_state
        if kill_chain_count >= 3 or has_exfil:
            stage_state = "confirmed_attack"
        elif kill_chain_count == 2:
            stage_state = "likely_attack"
        elif kill_chain_count == 1:
            stage_state = "suspicious"
        else:
            if has_ddos:
                # volumetric_ddos is handled separately
                max_ddos_sev = "info"
                for a in member_alerts:
                    if a.threat_type == "volumetric_ddos":
                        if a.severity in ("critical", "high"):
                            max_ddos_sev = "critical"
                
                if max_ddos_sev == "critical":
                    stage_state = "likely_attack"
                else:
                    stage_state = "suspicious"
            else:
                stage_state = "anomaly"

        # Determine current_stage
        current_stage = None
        if kill_chain_types_present:
            # Find the most advanced kill chain type
            for kc in reversed(KILL_CHAIN_ORDER):
                if kc in kill_chain_types_present:
                    current_stage = kc
                    break
        else:
            if has_ddos:
                current_stage = "volumetric_ddos"
            elif has_anomaly:
                current_stage = "unknown_threat"

        # forecast_next_stage / forecast_note
        forecast_next_stage = None
        forecast_note = None
        if current_stage in KILL_CHAIN_NEXT:
            next_stage = KILL_CHAIN_NEXT[current_stage]
            if next_stage:
                forecast_next_stage = next_stage
                forecast_note = FORECAST_NOTE

        # 5. persist the incident
        updates = {
            "updated_at": updated_at,
            "last_event_at": last_event_at,
            "member_alert_ids": member_alert_ids,
            "distinct_threat_types": distinct_threat_types,
            "risk_score": float(risk_score),
            "risk_breakdown": risk_breakdown,
            "stage_state": stage_state,
            "current_stage": current_stage,
            "forecast_next_stage": forecast_next_stage,
            "forecast_note": forecast_note
        }
        
        updated_incident = await incident_service.update_incident_fields(
            incident.incident_id,
            updates
        )
        
        return updated_incident
