import asyncio
from datetime import datetime, timezone
import uuid
from app.core.database import AsyncSessionLocal
from app.models.alert import Alert

async def insert_alert():
    async with AsyncSessionLocal() as session:
        new_alert = Alert(
            alert_id=uuid.uuid4(),
            detector_output_id=str(uuid.uuid4()),
            detector_id="ddos_detector",
            threat_type="volumetric_ddos",
            entity_type="source",
            entity_key="10.1.1.50",
            detected_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            first_seen_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
            status="new",
            severity="high",
            severity_candidate="high",
            confidence=0.95,
            score=95.0,
            title="Massive SYN Flood Detected",
            evidence_summary="10000 SYN packets in 1 second",
            evidence={},
            source_feature_references=[],
            detector_version="1.0.0",
            model_version="1.0.0",
            schema_version="1.0.0"
        )
        session.add(new_alert)
        await session.commit()
        print(f"Inserted alert: {new_alert.alert_id}")

if __name__ == "__main__":
    asyncio.run(insert_alert())
