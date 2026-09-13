import os
import json
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    from openai import AsyncOpenAI, OpenAIError
except ImportError:
    AsyncOpenAI = None

class ProgressionStage(BaseModel):
    name: str
    observed: bool

class NarrativeContext(BaseModel):
    alert_id: str
    detector_id: str
    threat_type: str
    severity: str
    confidence: float
    src_ip: str | None = None
    dst_ip: str | None = None
    evidence: dict = Field(default_factory=dict)
    explanation: str = ""
    progression_stages: list[ProgressionStage] = Field(default_factory=list)
    correlated_events: list[dict] = Field(default_factory=list)

SYSTEM_PROMPT = """You are a strict cybersecurity analyst for the Irochi threat detection system.
Your job is to generate a concise, factual incident narrative based ONLY on the provided structured alert data.

Rules:
1. DO NOT invent attacks, malware, compromised hosts, stolen data, attacker identity, or any missing kill-chain stages.
2. Distinguish observation from interpretation. (e.g. "observed periodic communication", not "malware is beaconing").
3. Use certainty language carefully: "observed", "detected", "potential", "consistent with", "available evidence suggests".
4. Do NOT use: "confirmed attack", "attacker compromised", "malware installed", "data stolen".
5. Keep it concise. 
6. Explain missing stages: If the available progression stages don't include later stages like Exfiltration, explicitly say: "Exfiltration was not observed in the available alert data."
7. Output MUST be valid JSON with the exact keys: "what_was_observed", "why_it_matters", "what_to_investigate".

JSON Schema:
{
    "what_was_observed": "...",
    "why_it_matters": "...",
    "what_to_investigate": "..."
}
"""

def _deterministic_fallback(context: NarrativeContext) -> dict:
    observed_stages = [s.name for s in context.progression_stages if s.observed]
    missing_stages = [s.name for s in context.progression_stages if not s.observed]
    
    stages_text = f"Observed stages include {', '.join(observed_stages)}." if observed_stages else "No clear progression chain established."
    missing_text = f" Stages such as {', '.join(missing_stages)} were not observed." if missing_stages else ""
    
    event_count = len(context.correlated_events)
    related_text = f" There are {event_count} total correlated events in this timeline." if event_count > 1 else ""

    return {
        "what_was_observed": f"Irochi detected {context.threat_type} activity originating from {context.src_ip or 'unknown source'}. {stages_text}{missing_text}{related_text}",
        "why_it_matters": context.explanation or "The observed evidence crossed configured detection thresholds.",
        "what_to_investigate": f"Review the correlated timeline events and check recent activity for {context.src_ip or 'the source'}. Verify if the destination is known or authorized."
    }

async def generate_attack_story(context: NarrativeContext) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not AsyncOpenAI:
        logger.info("OpenAI API key missing or openai package not installed. Using deterministic fallback.")
        return _deterministic_fallback(context)
        
    client = AsyncOpenAI(api_key=api_key)
    
    user_payload = {
        "primary_alert": {
            "threat_type": context.threat_type,
            "severity": context.severity,
            "confidence": context.confidence,
            "src_ip": context.src_ip,
            "dst_ip": context.dst_ip,
            "explanation": context.explanation,
        },
        "progression_stages": [{"name": s.name, "observed": s.observed} for s in context.progression_stages],
        "correlated_events_count": len(context.correlated_events),
        "evidence_summary": context.evidence
    }

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate the JSON narrative for this alert context:\n{json.dumps(user_payload)}"}
            ],
            response_format={"type": "json_object"},
            timeout=10.0,
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "what_was_observed": result.get("what_was_observed", ""),
            "why_it_matters": result.get("why_it_matters", ""),
            "what_to_investigate": result.get("what_to_investigate", "")
        }
    except Exception as e:
        logger.error(f"Error generating AI narrative: {e}. Falling back to deterministic.")
        return _deterministic_fallback(context)
