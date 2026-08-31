import pytest
from app.schemas.canonical import EventType, Protocol, SensorSource, TimestampPrecision
from app.services.ingest.normalizer import IngestNormalizer

@pytest.fixture
def normalizer():
    return IngestNormalizer()

def test_parse_conn(normalizer):
    zeek_record = {
        "ts": 1724848215.123,
        "uid": "Cw8M9x",
        "id.orig_h": "10.0.0.1",
        "id.resp_h": "10.0.0.2",
        "id.orig_p": 1234,
        "id.resp_p": 443,
        "proto": "tcp",
        "duration": 5.0,
        "orig_bytes": 100,
        "resp_bytes": 200,
        "orig_pkts": 2,
        "resp_pkts": 3,
        "conn_state": "S1",
        "history": "ShAD",
        "service": "ssl",
        "local_orig": True,
        "local_resp": False
    }

    event = normalizer.parse_conn(zeek_record)
    assert event is not None
    assert event.event_type == EventType.CONNECTION
    assert event.connection_id == "Cw8M9x"
    assert event.timestamp == 1724848215123000
    assert event.timestamp_precision == TimestampPrecision.MICROSECOND
    assert event.sensor_source == SensorSource.ZEEK
    assert event.src_ip == "10.0.0.1"
    assert event.dst_ip == "10.0.0.2"
    assert event.src_port == 1234
    assert event.dst_port == 443
    assert event.protocol == Protocol.TCP

    payload = event.payload
    assert payload.duration == 5.0
    assert payload.orig_bytes == 100
    assert payload.resp_bytes == 200
    assert payload.orig_pkts == 2
    assert payload.resp_pkts == 3
    assert payload.conn_state == "S1"
    assert payload.history == "ShAD"
    assert payload.service == "ssl"
    assert payload.local_orig is True

def test_parse_dns(normalizer):
    zeek_record = {
        "ts": 1724848215.123,
        "uid": "Cdns123",
        "id.orig_h": "10.0.0.1",
        "id.resp_h": "8.8.8.8",
        "proto": "udp",
        "query": "example.com",
        "qtype_name": "A",
        "qtype": 1,
        "rcode_name": "NOERROR",
        "rcode": 0,
        "answers": ["93.184.216.34"],
        "rejected": False,
        "trans_id": 12345,
        "rtt": 0.01
    }

    event = normalizer.parse_dns(zeek_record)
    assert event is not None
    assert event.event_type == EventType.DNS
    assert event.connection_id == "Cdns123"

    payload = event.payload
    assert payload.query == "example.com"
    assert payload.qtype_name == "A"
    assert payload.rcode == 0
    assert payload.answers == ["93.184.216.34"]
    assert payload.rtt == 0.01

def test_parse_ssl(normalizer):
    zeek_record = {
        "ts": 1724848215.123,
        "uid": "Cssl123",
        "id.orig_h": "10.0.0.1",
        "id.resp_h": "10.0.0.2",
        "proto": "tcp",
        "server_name": "example.com",
        "version": "TLSv1.3",
        "cipher": "TLS_AES_128_GCM_SHA256",
        "established": True
    }

    event = normalizer.parse_ssl(zeek_record)
    assert event is not None
    assert event.event_type == EventType.TLS

    payload = event.payload
    assert payload.server_name == "example.com"
    assert payload.version == "TLSv1.3"
    assert payload.established is True
    assert payload.ja3 is None  # Optional field without JA3 package

def test_malformed_zeek_record(normalizer):
    # Missing required fields like id.orig_h which creates validation errors for CanonicalEventEnvelope
    bad_record = {
        "ts": "not-a-number",
        "uid": "123"
    }
    # It should catch the validation error and return None
    event = normalizer.parse_conn(bad_record)
    assert event is None
