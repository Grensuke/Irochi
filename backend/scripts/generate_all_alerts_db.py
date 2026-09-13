import asyncio
import random
from datetime import datetime, timedelta, timezone
import uuid
from app.core.database import AsyncSessionLocal
from app.models.alert import Alert

THREATS = [
    ("volumetric_ddos", "ddos_detector", "critical"),
    ("recon_port_scan", "recon_detector", "medium"),
    ("dga_dns_tunnel", "dga_dns_detector", "high"),
    ("c2_beaconing", "tls_c2_detector", "high"),
    ("data_exfiltration", "exfil_detector", "critical")
]

IPS = ["10.0.0.1", "10.0.0.2", "192.168.1.100", "172.16.0.5"]

async def generate_alerts():
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        
        for _ in range(50):
            threat, detector, base_sev = random.choice(THREATS)
            
            # Spread over last 24 hours
            hours_ago = random.uniform(0, 23.5)
            detected = now - timedelta(hours=hours_ago)
            
            src = random.choice(IPS)
            dst = random.choice(IPS)
            while dst == src:
                dst = random.choice(IPS)
                
            conf = random.uniform(0.6, 0.99)
            
            new_alert = Alert(
                alert_id=uuid.uuid4(),
                detector_output_id=str(uuid.uuid4()),
                detector_id=detector,
                threat_type=threat,
                entity_type="source",
                entity_key=src,
                detected_at=detected,
                created_at=detected,
                first_seen_at=detected - timedelta(minutes=5),
                last_seen_at=detected,
                status="new",
                severity=base_sev,
                severity_candidate=base_sev,
                confidence=conf,
                score=conf * 100,
                title=f"Test {threat} Alert",
                evidence_summary="Generated for visual testing",
                evidence={"src_ip": src, "dst_ip": dst},
                source_feature_references=[],
                detector_version="1.0.0",
                model_version="1.0.0",
                schema_version="1.0.0"
            )
            session.add(new_alert)
            
        await session.commit()
        print("Inserted 50 test alerts across all threat types.")

if __name__ == "__main__":
    asyncio.run(generate_alerts())
