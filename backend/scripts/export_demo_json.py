import asyncio
import json
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.alert import Alert
from app.models.incident import Incident
from app.schemas.alerts import AlertResponse

async def export():
    async with AsyncSessionLocal() as session:
        result_alerts = await session.execute(select(Alert))
        alerts = result_alerts.scalars().all()
        
        result_incidents = await session.execute(select(Incident))
        incidents = result_incidents.scalars().all()
        
        alerts_json = []
        for a in alerts:
            d = AlertResponse.from_orm(a).model_dump(mode="json")
            alerts_json.append(d)
            
        with open("/app/demo_replay_alerts.json", "w") as f:
            json.dump(alerts_json, f, indent=2)
            
        # Incidents need a simple dump for now
        # Actually for Option 3 (Frontend Replay) we only need alerts to stream through WebSockets
        print(f"Exported {len(alerts_json)} alerts.")

if __name__ == "__main__":
    asyncio.run(export())
