import pytest
from app.services.ai_narrative import _deterministic_fallback, NarrativeContext, ProgressionStage

def test_deterministic_fallback():
    context = NarrativeContext(
        alert_id="123",
        detector_id="det_recon",
        threat_type="recon_portscan",
        severity="high",
        confidence=0.9,
        src_ip="192.168.1.5",
        dst_ip="10.0.0.1",
        explanation="Detected fast port scan.",
        progression_stages=[
            ProgressionStage(name="Reconnaissance", observed=True),
            ProgressionStage(name="Exfiltration", observed=False)
        ],
        correlated_events=[{}, {}] # 2 events
    )
    
    fallback = _deterministic_fallback(context)
    
    assert "what_was_observed" in fallback
    assert "why_it_matters" in fallback
    assert "what_to_investigate" in fallback
    
    # Check that it didn't invent anything
    assert "recon_portscan" in fallback["what_was_observed"]
    assert "192.168.1.5" in fallback["what_was_observed"]
    
    # Check progression logic
    assert "Reconnaissance" in fallback["what_was_observed"]
    assert "Exfiltration" in fallback["what_was_observed"]
    assert "not observed" in fallback["what_was_observed"]
    assert "2 total correlated events" in fallback["what_was_observed"]

def test_deterministic_fallback_no_stages():
    context = NarrativeContext(
        alert_id="123",
        detector_id="det_ddos",
        threat_type="volumetric_ddos",
        severity="critical",
        confidence=0.99,
        explanation="Massive traffic spike.",
    )
    
    fallback = _deterministic_fallback(context)
    assert "No clear progression chain established" in fallback["what_was_observed"]

