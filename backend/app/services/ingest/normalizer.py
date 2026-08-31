import logging
import time
import uuid
from typing import Any, Optional

from app.schemas.canonical import (
    ConnectionEvent,
    ConnectionPayload,
    DnsEvent,
    DnsPayload,
    EventType,
    Protocol,
    SensorSource,
    TimestampPrecision,
    TlsEvent,
    TlsPayload,
)

logger = logging.getLogger(__name__)


class IngestNormalizer:
    def __init__(self):
        self.schema_version = "1.0"

    def _get_protocol(self, proto: str) -> Protocol:
        proto_map = {
            "tcp": Protocol.TCP,
            "udp": Protocol.UDP,
            "icmp": Protocol.ICMP,
        }
        return proto_map.get(proto.lower(), Protocol.OTHER)

    def _create_envelope(
        self, record: dict[str, Any], event_type: EventType
    ) -> dict[str, Any]:
        """Create the canonical envelope from common Zeek fields."""
        # Zeek ts is a float (seconds since epoch)
        ts_float = float(record.get("ts", 0))
        ts_micro = int(ts_float * 1_000_000)

        # Zeek ID fields
        id_orig_h = record.get("id.orig_h") or record.get("id", {}).get("orig_h", "")
        id_resp_h = record.get("id.resp_h") or record.get("id", {}).get("resp_h", "")
        id_orig_p = record.get("id.orig_p") or record.get("id", {}).get("orig_p")
        id_resp_p = record.get("id.resp_p") or record.get("id", {}).get("resp_p")

        return {
            "event_id": str(uuid.uuid4()),
            "connection_id": record.get("uid", ""),
            "timestamp": ts_micro,
            "timestamp_precision": TimestampPrecision.MICROSECOND,
            "ingest_timestamp": int(time.time() * 1_000_000),
            "sensor_source": SensorSource.ZEEK,
            "src_ip": id_orig_h,
            "dst_ip": id_resp_h,
            "src_port": int(id_orig_p) if id_orig_p is not None else None,
            "dst_port": int(id_resp_p) if id_resp_p is not None else None,
            "protocol": self._get_protocol(record.get("proto", "")),
            "protocol_number": None,
            "schema_version": self.schema_version,
            "event_type": event_type,
        }

    def parse_conn(self, record: dict[str, Any]) -> Optional[ConnectionEvent]:
        try:
            envelope = self._create_envelope(record, EventType.CONNECTION)

            payload = ConnectionPayload(
                duration=record.get("duration"),
                orig_bytes=record.get("orig_bytes"),
                resp_bytes=record.get("resp_bytes"),
                orig_pkts=record.get("orig_pkts"),
                resp_pkts=record.get("resp_pkts"),
                conn_state=record.get("conn_state"),
                history=record.get("history"),
                tcp_flags=None,  # Zeek doesn't natively export cumulative flags by default
                service=record.get("service"),
                local_orig=record.get("local_orig"),
                local_resp=record.get("local_resp"),
            )

            envelope["payload"] = payload
            return ConnectionEvent(**envelope)
        except Exception as e:
            logger.warning(f"Failed to parse Zeek conn record: {e}")
            return None

    def parse_dns(self, record: dict[str, Any]) -> Optional[DnsEvent]:
        try:
            envelope = self._create_envelope(record, EventType.DNS)

            payload = DnsPayload(
                query=record.get("query", ""),
                qtype_name=record.get("qtype_name", ""),
                qtype=record.get("qtype"),
                rcode_name=record.get("rcode_name"),
                rcode=record.get("rcode"),
                answers=record.get("answers"),
                rejected=record.get("rejected"),
                trans_id=record.get("trans_id"),
                rtt=record.get("rtt"),
            )

            envelope["payload"] = payload
            return DnsEvent(**envelope)
        except Exception as e:
            logger.warning(f"Failed to parse Zeek dns record: {e}")
            return None

    def parse_ssl(self, record: dict[str, Any]) -> Optional[TlsEvent]:
        try:
            envelope = self._create_envelope(record, EventType.TLS)

            payload = TlsPayload(
                ja3=record.get("ja3"),
                ja3s=record.get("ja3s"),
                ja4=record.get("ja4"),
                ja4s=record.get("ja4s"),
                server_name=record.get("server_name"),
                version=record.get("version"),
                cipher=record.get("cipher"),
                established=record.get("established"),
                validation_status=record.get("validation_status"),
                subject=record.get("subject"),
                issuer=record.get("issuer"),
            )

            envelope["payload"] = payload
            return TlsEvent(**envelope)
        except Exception as e:
            logger.warning(f"Failed to parse Zeek ssl record: {e}")
            return None
