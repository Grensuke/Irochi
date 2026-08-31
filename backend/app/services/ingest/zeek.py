import json
import logging
import subprocess
import tempfile
from pathlib import Path

from app.schemas.canonical import EventType
from app.services.ingest.normalizer import IngestNormalizer
from app.services.streaming.producer import KafkaProducerService

logger = logging.getLogger(__name__)


class ZeekIngestPipeline:
    def __init__(self, kafka_bootstrap_servers: str = "localhost:19092"):
        self.normalizer = IngestNormalizer()
        self.kafka_bootstrap_servers = kafka_bootstrap_servers

        self.TOPIC_CONNECTION = "irochi.events.connection.v1"
        self.TOPIC_DNS = "irochi.events.dns.v1"
        self.TOPIC_TLS = "irochi.events.tls.v1"

    def run_zeek_on_pcap(self, pcap_path: str, bpf_filter: str = None) -> Path:
        """
        Runs Zeek on a PCAP file using a temporary Docker container and a scratch output dir.
        Returns the path to the output directory containing JSON logs.
        """
        pcap_path = Path(pcap_path).resolve()
        if not pcap_path.exists():
            raise FileNotFoundError(f"PCAP not found: {pcap_path}")

        # Create a temp directory for logs
        output_dir = Path(tempfile.mkdtemp(prefix="zeek_logs_"))

        # Zeek command with JSON output
        filter_arg = f"-f '{bpf_filter}'" if bpf_filter else ""

        cmd = [
            "docker", "run", "--rm",
            "-v", f"{pcap_path.parent}:/pcap_dir",
            "-v", f"{output_dir}:/logs",
            "-w", "/logs",
            "blacktop/zeek:latest",
            "-C", "-r", f"/pcap_dir/{pcap_path.name}", "LogAscii::use_json=T"
        ]

        if bpf_filter:
            cmd.extend(["-f", bpf_filter])

        logger.info(f"Running Zeek on {pcap_path.name} to {output_dir}")
        subprocess.run(cmd, check=True, capture_output=True)
        return output_dir

    def parse_log_file(self, log_path: Path, event_type: EventType):
        """Yields canonical events from a specific Zeek JSON log file."""
        if not log_path.exists():
            return

        with open(log_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if event_type == EventType.CONNECTION:
                        event = self.normalizer.parse_conn(record)
                    elif event_type == EventType.DNS:
                        event = self.normalizer.parse_dns(record)
                    elif event_type == EventType.TLS:
                        event = self.normalizer.parse_ssl(record)
                    else:
                        event = None

                    if event is not None:
                        yield event
                except json.JSONDecodeError:
                    logger.warning(f"Malformed JSON in {log_path.name}: {line}")
                except Exception as e:
                    logger.warning(f"Error parsing record from {log_path.name}: {e}")

    async def ingest_to_redpanda(self, events) -> dict:
        """Publishes canonical events to Redpanda and returns counts."""
        producer = KafkaProducerService(self.kafka_bootstrap_servers)
        await producer.start()

        counts = {
            EventType.CONNECTION: 0,
            EventType.DNS: 0,
            EventType.TLS: 0,
        }

        try:
            for event in events:
                topic = None
                if event.event_type == EventType.CONNECTION:
                    topic = self.TOPIC_CONNECTION
                elif event.event_type == EventType.DNS:
                    topic = self.TOPIC_DNS
                elif event.event_type == EventType.TLS:
                    topic = self.TOPIC_TLS

                if topic and event.src_ip:
                    # Message key is src_ip
                    payload = event.model_dump()
                    await producer.send_message(topic, event.src_ip, payload)
                    counts[event.event_type] += 1
        finally:
            await producer.stop()

        return counts

    async def run_pipeline(self, pcap_path: str, bpf_filter: str = None) -> dict:
        """End-to-end prototype execution."""
        log_dir = self.run_zeek_on_pcap(pcap_path, bpf_filter)

        events = []
        for event in self.parse_log_file(log_dir / "conn.log", EventType.CONNECTION):
            events.append(event)
        for event in self.parse_log_file(log_dir / "dns.log", EventType.DNS):
            events.append(event)
        for event in self.parse_log_file(log_dir / "ssl.log", EventType.TLS):
            events.append(event)

        counts = await self.ingest_to_redpanda(events)
        return counts
