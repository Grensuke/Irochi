from fastapi import APIRouter
from app.services.ai_narrative import generate_attack_story, NarrativeContext

router = APIRouter()

@router.post("/generate")
async def generate_narrative(context: NarrativeContext):
    """
    Generates a grounded AI narrative based purely on deterministic evidence.
    Falls back to a deterministic string if AI is unavailable.
    """
    narrative = await generate_attack_story(context)
    return narrative
