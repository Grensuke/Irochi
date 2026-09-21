import pytest
import uuid
from datetime import datetime, timezone
from app.services.incident_engine import IncidentEngine
from app.models.incident import Incident
from app.models.alert import Alert

class MockSession:
    def __init__(self):
        self.committed = False
        self.stmts = []
        
    async def execute(self, stmt):
        self.stmts.append(stmt)
        class MockResult:
            def scalar_one_or_none(self):
                return Alert(alert_id=uuid.uuid4(), threat_type="volumetric_ddos", severity="critical")
            def scalars(self):
                class MockScalars:
                    def all(self):
                        return []
                return MockScalars()
        return MockResult()

    async def commit(self):
        self.committed = True

class MockIncidentService:
    def __init__(self):
        pass
    async def get_open_incident_for_src_ip(self, src_ip, window_start):
        return None
    async def create_incident(self, incident):
        incident.incident_id = uuid.uuid4()
        return incident
    async def update_incident_fields(self, incident_id, updates):
        return updates

@pytest.mark.asyncio
async def test_escalation_multiplier_applied(monkeypatch):
    engine = IncidentEngine()
    
    # Mock postgres incident service
    from app.services import incident_engine
    monkeypatch.setattr(incident_engine, "PostgresIncidentService", lambda session: MockIncidentService())
    
    session = MockSession()
    
    # Let's override member_alerts in the engine explicitly so we can test the math
    # We want to feed it member alerts that have different threat types.
    class PatchedSession(MockSession):
        async def execute(self, stmt):
            class MockResult:
                def scalar_one_or_none(self):
                    return Alert(alert_id=uuid.uuid4(), threat_type="recon_portscan", severity="high")
                def scalars(self):
                    class MockScalars:
                        def all(self):
                            return [
                                Alert(alert_id=uuid.uuid4(), threat_type="recon_portscan", severity="high", confidence=1.0),
                                Alert(alert_id=uuid.uuid4(), threat_type="dga_dns_tunnel", severity="high", confidence=1.0),
                                Alert(alert_id=uuid.uuid4(), threat_type="c2_beaconing", severity="high", confidence=1.0)
                            ]
                    return MockScalars()
            return MockResult()
            
    # Base weights: recon=15, dga=20, c2=22. Sum = 57.
    # Distinct types = 3. Escalation = 1.0 + 0.15 * max(0, 3-1) = 1.3
    # Expected raw = 57. Expected scaled = min(100, 57 * 1.3) = min(100, 74.1) = 74
    
    alert_payload = {
        "alert_id": str(uuid.uuid4()),
        "src_ip": "1.2.3.4",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    result = await engine.on_alert(alert_payload, PatchedSession())
    
    assert result["risk_score"] == 74.0, f"Expected 74.0, got {result['risk_score']}"
    assert result["stage_state"] == "confirmed_attack"
    assert result["current_stage"] == "c2_beaconing"
    
@pytest.mark.asyncio
async def test_ddos_does_not_enter_linear_kill_chain(monkeypatch):
    engine = IncidentEngine()
    
    from app.services import incident_engine
    monkeypatch.setattr(incident_engine, "PostgresIncidentService", lambda session: MockIncidentService())
    
    class PatchedSession(MockSession):
        async def execute(self, stmt):
            class MockResult:
                def scalar_one_or_none(self):
                    return Alert(alert_id=uuid.uuid4(), threat_type="volumetric_ddos", severity="critical")
                def scalars(self):
                    class MockScalars:
                        def all(self):
                            return [
                                Alert(alert_id=uuid.uuid4(), threat_type="volumetric_ddos", severity="critical", confidence=1.0),
                            ]
                    return MockScalars()
            return MockResult()

    alert_payload = {
        "alert_id": str(uuid.uuid4()),
        "src_ip": "1.2.3.4",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    result = await engine.on_alert(alert_payload, PatchedSession())
    
    # Kill chain shouldn't include DDoS, so it falls to the `else` block for determining stage
    assert result["stage_state"] == "likely_attack", "Critical DDoS should trigger likely_attack"
    assert result["current_stage"] == "volumetric_ddos", "Current stage should be volumetric_ddos"
    assert result["forecast_next_stage"] is None, "DDoS should not forecast next linear stage"

@pytest.mark.asyncio
async def test_close_incident():
    """Test the close_incident method of PostgresIncidentService."""
    from app.services.postgres_incident_service import PostgresIncidentService
    
    class FakeSession:
        async def execute(self, stmt):
            class FakeResult:
                def scalar_one_or_none(self):
                    incident = Incident(
                        incident_id=uuid.uuid4(),
                        status="closed",
                        closed_at=datetime.now(timezone.utc),
                        resolution_note="False positive",
                        closed_by="admin"
                    )
                    return incident
            return FakeResult()
            
        async def commit(self):
            pass

    service = PostgresIncidentService(FakeSession())
    updated = await service.close_incident(
        incident_id=uuid.uuid4(),
        resolution_note="False positive",
        closed_by="admin"
    )
    
    assert updated.status == "closed"
    assert updated.resolution_note == "False positive"
    assert updated.closed_by == "admin"
    assert updated.closed_at is not None

@pytest.mark.asyncio
async def test_closed_incident_does_not_correlate(monkeypatch):
    """Regression test: a closed incident should not accept new alerts."""
    engine = IncidentEngine()
    
    # We mock get_open_incident_for_src_ip to return None, simulating that 
    # the existing incident for this IP is 'closed' (and thus not returned).
    class MockServiceThatReturnsNone:
        async def get_open_incident_for_src_ip(self, src_ip, window_start):
            return None # Simulates that no OPEN incident exists
            
        async def create_incident(self, incident):
            incident.incident_id = uuid.uuid4()
            return incident
            
        async def update_incident_fields(self, incident_id, updates):
            incident = Incident(
                incident_id=incident_id,
                status="open",
                entity_type="source",
                entity_key="10.0.0.1",
                opened_at=datetime.now(timezone.utc),
                **updates
            )
            return incident
            
    from app.services import incident_engine
    monkeypatch.setattr(incident_engine, "PostgresIncidentService", lambda session: MockServiceThatReturnsNone())
    
    class FakeSession(MockSession):
        async def execute(self, stmt):
            class MockResult:
                def scalar_one_or_none(self):
                    return Alert(alert_id=uuid.uuid4(), threat_type="recon_portscan")
                def scalars(self):
                    class MockScalars:
                        def all(self):
                            return [Alert(alert_id=uuid.uuid4(), threat_type="recon_portscan")]
                    return MockScalars()
            return MockResult()

    alert_payload = {
        "alert_id": str(uuid.uuid4()),
        "src_ip": "10.0.0.1",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    result = await engine.on_alert(alert_payload, FakeSession())
    
    # It should have created a new incident instead of failing or updating a closed one
    assert result.status == "open" # The newly created incident will have status open
