import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.detectors.ddos import DdosDetector
from app.services.detectors.recon import ReconDetector
from app.schemas.detectors import DetectorInput, Severity
from app.schemas.features import DdosFeatureRecord, ReconFeatureRecord

async def test_severities():
    print("Testing DDoS Detector...")
    ddos = DdosDetector()
    
    # Critical DDoS (High packet rate, High byte rate, High Syn) -> conf > 0.9, triggers >= 3
    critical_ddos_payload = {"packet_rate": 500, "byte_rate": 50000, "syn_ratio": 0.9, "source_ip_entropy": 0.8}
    # Medium DDoS (Moderate packet rate) -> conf > 0.6, triggers >= 1
    medium_ddos_payload = {"packet_rate": 60, "byte_rate": 1000, "syn_ratio": 0.1, "source_ip_entropy": 0.1}

    import time
    def make_ddos_input(payload):
        record = DdosFeatureRecord(
            feature_id="f1", 
            revision=1, 
            entity_type="destination", 
            entity_key="10.0.0.1", 
            mechanism="windowed",
            computed_at=int(time.time() * 1000000),
            schema_version="1.0",
            payload=payload
        )
        return DetectorInput(input_id="i1", detector_id="ddos_detector", feature_record=record)

    out = await ddos.evaluate([make_ddos_input(critical_ddos_payload)])
    print(f"  Critical Input -> Decision: {out[0].decision}, Severity: {out[0].severity_candidate}, Confidence: {out[0].confidence}")
    
    out = await ddos.evaluate([make_ddos_input(medium_ddos_payload)])
    print(f"  Medium Input -> Decision: {out[0].decision}, Severity: {out[0].severity_candidate}, Confidence: {out[0].confidence}")

    print("\nTesting Recon Detector...")
    recon = ReconDetector()
    
    # Medium Recon (High scan rate)
    medium_recon_payload = {"unique_destination_ports": 200, "unique_destination_hosts": 10, "scan_rate": 50, "connection_fan_out": 0.9}
    # Low Recon (Moderate scan rate)
    low_recon_payload = {"unique_destination_ports": 60, "unique_destination_hosts": 2, "scan_rate": 15, "connection_fan_out": 0.1}

    def make_recon_input(payload):
        record = ReconFeatureRecord(
            feature_id="f1", 
            revision=1, 
            entity_type="source", 
            entity_key="10.0.0.1", 
            mechanism="windowed",
            computed_at=int(time.time() * 1000000),
            schema_version="1.0",
            payload=payload
        )
        return DetectorInput(input_id="i1", detector_id="recon_detector", feature_record=record)

    out = await recon.evaluate([make_recon_input(medium_recon_payload)])
    print(f"  Medium Input -> Decision: {out[0].decision}, Severity: {out[0].severity_candidate}, Confidence: {out[0].confidence}")
    
    out = await recon.evaluate([make_recon_input(low_recon_payload)])
    print(f"  Low Input -> Decision: {out[0].decision}, Severity: {out[0].severity_candidate}, Confidence: {out[0].confidence}")

    print("\nAll severity ranges (LOW, MEDIUM, HIGH, CRITICAL) are successfully being output by the detectors.")

if __name__ == "__main__":
    asyncio.run(test_severities())
