import asyncio
import random
from datetime import datetime, timedelta, timezone
import uuid
import math
from app.core.database import AsyncSessionLocal
from app.models.alert import Alert
from app.models.incident import Incident
from sqlalchemy import text

THREAT_TYPES = [
    ("recon_portscan", "recon_detector", "medium"),
    ("c2_beaconing", "tls_c2_detector", "high"),
    ("dga_dns_tunnel", "dns_dga_tunnel_detector", "high"),
    ("data_exfiltration", "exfiltration_detector", "critical"),
    ("volumetric_ddos", "ddos_detector", "critical"),
    ("encrypted_malware", "tls_c2_detector", "high"),
    ("novel_anomaly", "anomaly_detector", "medium"),
]

async def reset_data():
    now = datetime.now(timezone.utc)
    
    async with AsyncSessionLocal() as session:
        # 1. Clear all data
        await session.execute(text("TRUNCATE TABLE alerts, incidents CASCADE"))
        
        # 2. Add 3 to 5 threats of each type
        for threat, detector, sev in THREAT_TYPES:
            num_incidents = random.randint(3, 5)
            for _ in range(num_incidents):
                incident_id = uuid.uuid4()
                src_ip = f"192.168.1.{random.randint(10,250)}"
                dst_ip = f"10.0.0.{random.randint(10,250)}"
                
                num_alerts = random.randint(1, 3)
                alert_ids = []
                
                # Base time for this incident
                ts_base = now - timedelta(hours=random.randint(0, 24), minutes=random.randint(0, 59))
                
                for i in range(num_alerts):
                    alert_id = uuid.uuid4()
                    alert_ids.append(str(alert_id))
                    ts = ts_base + timedelta(minutes=i*2)
                    
                    new_alert = Alert(
                        alert_id=alert_id,
                        incident_id=incident_id,
                        detector_output_id=str(uuid.uuid4()),
                        detector_id=detector,
                        threat_type=threat,
                        entity_type="source",
                        entity_key=src_ip,
                        detected_at=ts,
                        created_at=ts,
                        first_seen_at=ts - timedelta(minutes=5),
                        last_seen_at=ts,
                        status="new",
                        severity=sev,
                        severity_candidate=sev,
                        confidence=random.uniform(0.7, 0.99),
                        score=random.uniform(70, 99),
                        title=f"Detected {threat}",
                        evidence_summary="Generated for visual testing",
                        evidence={"src_ip": src_ip, "dst_ip": dst_ip, "observation": "Synthetic anomaly"},
                        source_feature_references=[],
                        detector_version="1.0.0",
                        model_version="1.0.0",
                        schema_version="1.0.0"
                    )
                    session.add(new_alert)
                
                stage_state = 'anomaly' if sev == 'low' else 'suspicious' if sev == 'medium' else 'likely_attack' if sev == 'high' else 'confirmed_attack'
                
                new_incident = Incident(
                    incident_id=incident_id,
                    entity_type="source",
                    entity_key=src_ip,
                    status="open",
                    opened_at=ts_base,
                    updated_at=ts_base + timedelta(minutes=num_alerts*2),
                    last_event_at=ts_base + timedelta(minutes=num_alerts*2),
                    member_alert_ids=alert_ids,
                    distinct_threat_types=[threat],
                    risk_score=random.uniform(50, 99),
                    risk_breakdown={threat: random.uniform(50, 99)},
                    stage_state=stage_state,
                    current_stage=threat,
                    forecast_next_stage=None,
                    forecast_note=None
                )
                session.add(new_incident)
                
        await session.commit()
        print("Demo timeline populated successfully.")

if __name__ == "__main__":
    asyncio.run(reset_data())
