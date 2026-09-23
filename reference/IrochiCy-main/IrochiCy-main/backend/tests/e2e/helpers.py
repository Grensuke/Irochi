import asyncio
import json
import random
import time
from datetime import datetime
from uuid import uuid4

import httpx


def build_detector_result(
    threat_type: str,
    src_ip: str,
    confidence: float,
    dst_ip: str = "192.168.1.1",
    dst_port: int = 443,
    protocol: str = "TCP",
) -> dict:
    """Build a valid DetectorResult dict for a given threat type,
    auto-populating realistic evidence based on threat_type."""

    evidence_map = {
        "ddos": [
            {
                "signal_name": "packet_rate",
                "signal_type": "derived",
                "value": random.randint(10000, 80000),
                "threshold": 10000.0,
                "triggered": True,
            },
            {
                "signal_name": "syn_ratio",
                "signal_type": "derived",
                "value": round(random.uniform(0.86, 0.99), 2),
                "threshold": 0.85,
                "triggered": True,
            },
        ],
        "recon": [
            {
                "signal_name": "unique_dst_ports",
                "signal_type": "derived",
                "value": random.randint(1001, 5000),
                "threshold": 1000.0,
                "triggered": True,
            },
            {
                "signal_name": "scan_rate",
                "signal_type": "derived",
                "value": round(random.uniform(51, 150), 1),
                "threshold": 50.0,
                "triggered": True,
            },
        ],
        "dns_dga": [
            {
                "signal_name": "domain_entropy",
                "signal_type": "derived",
                "value": round(random.uniform(3.9, 5.5), 2),
                "threshold": 3.8,
                "triggered": True,
            },
            {
                "signal_name": "n_gram_score",
                "signal_type": "derived",
                "value": round(random.uniform(0.01, 0.14), 3),
                "threshold": 0.15,
                "triggered": True,
            },
        ],
        "tls_c2": [
            {
                "signal_name": "ja3_blacklist_match",
                "signal_type": "intel",
                "value": True,
                "threshold": None,
                "triggered": True,
            },
            {
                "signal_name": "beacon_periodicity",
                "signal_type": "derived",
                "value": round(random.uniform(0.91, 0.99), 2),
                "threshold": 0.90,
                "triggered": True,
            },
        ],
        "exfiltration": [
            {
                "signal_name": "outbound_inbound_ratio",
                "signal_type": "derived",
                "value": round(random.uniform(10.1, 25.0), 1),
                "threshold": 10.0,
                "triggered": True,
            },
            {
                "signal_name": "rolling_transfer_bytes",
                "signal_type": "derived",
                "value": random.randint(524288000, 2147483648),
                "threshold": 524288000.0,
                "triggered": True,
            },
        ],
    }

    return {
        "event_id": str(uuid4()),
        "threat_type": threat_type,
        "detector_id": f"{threat_type}-detector-v1",
        "confidence": confidence,
        "evidence": evidence_map[threat_type],
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": random.randint(1024, 65535),
        "dst_port": dst_port,
        "protocol": protocol,
        "sensor_source": "zeek",
        "schema_version": "1.0.0",
        "detected_at": datetime.utcnow().isoformat(),
    }


async def poll_for_alert(
    client: httpx.AsyncClient,
    headers: dict,
    src_ip: str,
    threat_type: str,
    timeout_seconds: int = 20,
) -> dict:
    """Poll GET /alerts/ until an alert matching src_ip+threat_type appears.
    Returns the alert dict. Raises TimeoutError if not found."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        resp = await client.get(
            "/alerts/",
            params={"src_ip": src_ip, "threat_type": threat_type},
            headers=headers,
        )
        data = resp.json()
        if data.get("total", 0) > 0:
            return data["items"][0]
        await asyncio.sleep(1.0)
    raise TimeoutError(
        f"Alert not found for src_ip={src_ip} threat_type={threat_type} "
        f"after {timeout_seconds}s"
    )
