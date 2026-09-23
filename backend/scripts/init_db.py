import asyncio
import os
from app.core.database import engine
from app.models.base import Base

# Make sure all models are imported so Base knows about them
from app.models.alert import Alert
from app.models.incident import Incident

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_models())
