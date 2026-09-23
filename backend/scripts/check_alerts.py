import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://vibhinetra:change-me@localhost:5432/vibhinetra")
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10"))
        rows = result.mappings().all()
        
        print(f"Found {len(rows)} alerts.")
        for row in rows:
            print(f"--- Alert ID: {row['alert_id']} ---")
            print(f"Detector ID: {row['detector_id']}")
            print(f"Threat Type: {row['threat_type']}")
            print(f"Entity: {row['entity_type']} - {row['entity_key']}")
            print(f"Confidence: {row['confidence']}")
            print(f"Evidence:")
            print(json.dumps(row['evidence'], indent=2))
            print("\n")

if __name__ == "__main__":
    asyncio.run(main())
