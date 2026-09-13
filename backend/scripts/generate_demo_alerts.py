import asyncio
import random
from datetime import datetime, timedelta, timezone
import uuid
import math
from app.core.database import AsyncSessionLocal
from app.models.alert import Alert

async def insert_alert(session, threat, detector, sev, src, dst, conf, detected, title, evidence):
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
        severity=sev,
        severity_candidate=sev,
        confidence=conf,
        score=conf * 100,
        title=title,
        evidence_summary="Generated for visual testing",
        evidence=evidence,
        source_feature_references=[],
        detector_version="1.0.0",
        model_version="1.0.0",
        schema_version="1.0.0"
    )
    session.add(new_alert)

async def generate_demo_timeline():
    now = datetime.now(timezone.utc)
    
    async with AsyncSessionLocal() as session:
        # Phase 1: Ambient Noise (T-24h to Now)
        # Constant low volume port scanning across the whole timeline
        for h in range(0, 24):
            for _ in range(random.randint(1, 3)):
                ts = now - timedelta(hours=h, minutes=random.randint(0, 59))
                await insert_alert(
                    session, "recon_portscan", "recon_detector", "low", 
                    f"203.0.113.{random.randint(1,20)}", "10.0.0.1", 
                    random.uniform(0.5, 0.6), ts, 
                    "Low-intensity background scan", {"src_ip": f"203.0.113.{random.randint(1,20)}", "dst_ip": "10.0.0.1"}
                )

        # Phase 2: Aggressive Recon (T-20h to T-14h)
        # We want a distinct spike or hill shape around T-17h
        for h in range(14, 21):
            # Peak at 17
            dist = abs(17 - h)
            count = max(0, int(15 - (dist * 4))) 
            for _ in range(count):
                ts = now - timedelta(hours=h, minutes=random.randint(0, 59))
                await insert_alert(
                    session, "recon_portscan", "recon_detector", "medium", 
                    "198.51.100.45", f"10.0.0.{random.randint(2, 50)}", 
                    random.uniform(0.7, 0.9), ts, 
                    "Aggressive TCP SYN Scan", {"src_ip": "198.51.100.45", "dst_ip": f"10.0.0.{random.randint(2, 50)}"}
                )

        # Phase 3: C2 Beaconing (T-14h to Now)
        # Steady, highly periodic drumbeat from the compromised host
        for h in range(0, 15):
            for _ in range(8):
                ts = now - timedelta(hours=h, minutes=random.randint(0, 59))
                await insert_alert(
                    session, "c2_beaconing", "tls_c2_detector", "high", 
                    "10.0.0.24", "198.51.100.45", 
                    random.uniform(0.85, 0.95), ts, 
                    "Suspicious TLS Beacon to known malicious IP", {"src_ip": "10.0.0.24", "dst_ip": "198.51.100.45"}
                )
                
        # Phase 4: Data Exfiltration (T-10h to T-4h)
        # A large smooth hill in the middle-right of the graph
        for h in range(4, 11):
            dist = abs(7 - h)
            count = max(0, int(25 - (dist * 6)))
            for _ in range(count):
                ts = now - timedelta(hours=h, minutes=random.randint(0, 59))
                await insert_alert(
                    session, "data_exfiltration", "exfiltration_detector", "critical", 
                    "10.0.0.24", "198.51.100.45", 
                    random.uniform(0.9, 0.99), ts, 
                    "High Volume Outbound Transfer", {"src_ip": "10.0.0.24", "dst_ip": "198.51.100.45", "bytes_out": int(random.uniform(1e6, 5e6))}
                )

        # Phase 5: DGA DNS Tunneling (T-8h to Now)
        for h in range(0, 9):
            count = 10 - h
            for _ in range(count):
                ts = now - timedelta(hours=h, minutes=random.randint(0, 59))
                await insert_alert(
                    session, "dga_dns_tunnel", "dns_dga_tunnel_detector", "high", 
                    "10.0.0.24", "8.8.8.8", 
                    random.uniform(0.8, 0.95), ts, 
                    "DNS Tunneling / DGA Domain resolution", {"src_ip": "10.0.0.24", "dst_ip": "8.8.8.8", "query": f"{uuid.uuid4().hex[:12]}.com"}
                )
            
        # Phase 6: Volumetric DDoS (T-4h to Now)
        # Ramping up heavily to right now
        for h in range(0, 5):
            count = int((5 - h) * 12)
            for _ in range(count):
                ts = now - timedelta(hours=h, minutes=random.randint(0, 59))
                await insert_alert(
                    session, "volumetric_ddos", "ddos_detector", "critical", 
                    f"botnet-ip-{random.randint(1,100)}", "203.0.113.10", 
                    random.uniform(0.95, 1.0), ts, 
                    "Massive SYN Flood", {"src_ip": f"192.168.1.{random.randint(1,250)}", "dst_ip": "203.0.113.10"}
                )

        await session.commit()
        print("Demo timeline populated successfully.")

if __name__ == "__main__":
    asyncio.run(generate_demo_timeline())
