import uuid
import time
from typing import Optional, Dict, Any, Tuple
from app.schemas.canonical import CanonicalEvent, EventType
from app.schemas.features import (
    FeatureMechanism, FeatureRecord, FeatureRecordEnvelope,
    DetectorDomain, EntityType, WindowType, CorrelationStatus,
    DnsFeaturePayload, DnsFeatureRecord,
    TlsC2FeaturePayload, TlsC2FeatureRecord,
    ReconFeaturePayload, ReconFeatureRecord
)
from app.services.features.state import FeatureStateAdapter
from app.services.features.keys import build_entity_key

"""
IMPLEMENTATION STATUS:
- The generic reusable FeatureEngine is implemented and structurally capable of supporting all five detector domains.
- The currently supported mechanisms (enrichment, sliding, tumbling, correlation) are wired for a minimal slice of features to prove the architecture.
- Additional feature-domain wiring can be added incrementally.
- Detector logic is intentionally NOT implemented here.
"""

# --- M3.10 Revision / Provenance Boundary ---
async def build_envelope(
    state_adapter: FeatureStateAdapter,
    event: CanonicalEvent,
    mechanism: FeatureMechanism,
    detector_domain: DetectorDomain,
    entity_type: EntityType,
    entity_key: str,
    window_type: Optional[WindowType] = None,
    window_start: Optional[int] = None,
    window_end: Optional[int] = None
) -> dict:
    """Builds the common envelope for a feature record, handling revision and provenance."""
    # M3.10 Revision generation
    # The exact revision/staleness/idempotency mechanism remains OPEN.
    # This delegates to the state adapter's local development implementation.
    revision = await state_adapter.get_revision(entity_type, entity_key)

    # M3.10 Provenance strategy (Open, but we preserve raw event references)
    provenance = {
        "source_events": [event.event_id],
        "sensor_source": event.sensor_source.value,
        "ingest_timestamp": event.ingest_timestamp
    }

    return {
        "feature_id": str(uuid.uuid4()),
        "mechanism": mechanism,
        "detector_domain": detector_domain,
        "entity_type": entity_type,
        "entity_key": entity_key,
        "window_type": window_type,
        "window_start": window_start,
        "window_end": window_end,
        "computed_at": int(time.time() * 1000000), # microseconds
        "schema_version": "1.0",
        "revision": revision,
        "provenance": provenance
    }

# --- M3.5 Enrichment Mechanism ---
async def process_enrichment(
    state_adapter: FeatureStateAdapter,
    event: CanonicalEvent,
    detector_domain: DetectorDomain,
    entity_type: EntityType
) -> Optional[FeatureRecord]:
    """Processes a single event into an enrichment feature record."""
    try:
        entity_key = build_entity_key(entity_type, event.src_ip, event.dst_ip, event.connection_id)
    except ValueError:
        return None # Safely fail on missing context

    envelope_args = await build_envelope(
        state_adapter, event, FeatureMechanism.ENRICHMENT,
        detector_domain, entity_type, entity_key
    )

    # Simple explicit mapping based on domain (avoiding deep detector logic)
    if detector_domain == DetectorDomain.DNS and event.event_type == EventType.DNS:
        payload = DnsFeaturePayload(
            domain_entropy=None, # Mock calculation
            query_length=len(event.payload.query) if event.payload.query else 0,
            n_gram_score=None,
            label_count=len(event.payload.query.split(".")) if event.payload.query else 0,
            max_label_length=max([len(l) for l in event.payload.query.split(".")]) if event.payload.query else 0
        )
        return DnsFeatureRecord(**envelope_args, payload=payload)

    if detector_domain == DetectorDomain.TLS_C2 and event.event_type == EventType.TLS:
        # ja3_blacklist_match is external intelligence, we just preserve the field
        payload = TlsC2FeaturePayload(
            ja3_blacklist_match=None # Missing/Unknown during enrichment unless looked up
        )
        return TlsC2FeatureRecord(**envelope_args, payload=payload)

    return None

# --- M3.6 Sliding Mechanism ---
async def process_sliding(
    state_adapter: FeatureStateAdapter,
    event: CanonicalEvent,
    detector_domain: DetectorDomain,
    entity_type: EntityType,
    bucket_width_sec: int,
    window_size_sec: int
) -> Optional[FeatureRecord]:
    """
    Processes an event into a sliding window feature record.
    The exact window durations remain OPEN and must be supplied by configuration.
    """
    try:
        entity_key = build_entity_key(entity_type, event.src_ip, event.dst_ip, event.connection_id)
    except ValueError:
        return None

    # Determine time bucket
    event_sec = event.timestamp // 1000000
    current_bucket = (event_sec // bucket_width_sec) * bucket_width_sec

    # M3.9 Tier 1/Tier 2 handling
    # E.g. DNS sliding window for query frequency
    increments = {}
    if detector_domain == DetectorDomain.DNS and event.event_type == EventType.DNS:
        increments["query_count"] = 1

    if not increments:
        return None

    # Update state
    await state_adapter.increment_sliding_bucket(
        entity_type, entity_key, current_bucket, increments, ttl_seconds=window_size_sec*2
    )

    # Evaluate window
    active_buckets = [current_bucket - (i * bucket_width_sec) for i in range(window_size_sec // bucket_width_sec)]
    bucket_states = await state_adapter.get_sliding_buckets(entity_type, entity_key, active_buckets)

    # Aggregate
    total_queries = 0
    for state in bucket_states:
        if state and "query_count" in state:
            total_queries += int(state["query_count"])

    envelope_args = await build_envelope(
        state_adapter, event, FeatureMechanism.WINDOWED,
        detector_domain, entity_type, entity_key,
        window_type=WindowType.SLIDING,
        window_start=(current_bucket - window_size_sec + bucket_width_sec) * 1000000,
        window_end=(current_bucket + bucket_width_sec) * 1000000
    )

    if detector_domain == DetectorDomain.DNS:
        # query_frequency = queries / window_size_sec
        payload = DnsFeaturePayload(
            query_frequency=total_queries / window_size_sec
        )
        return DnsFeatureRecord(**envelope_args, payload=payload)

    return None

# --- M3.7 Tumbling Mechanism ---
async def process_tumbling(
    state_adapter: FeatureStateAdapter,
    event: CanonicalEvent,
    detector_domain: DetectorDomain,
    entity_type: EntityType,
    window_size_sec: int
) -> Optional[FeatureRecord]:
    """
    Processes an event into a tumbling window feature record.
    The exact window durations remain OPEN and must be supplied by configuration.
    """
    try:
        entity_key = build_entity_key(entity_type, event.src_ip, event.dst_ip, event.connection_id)
    except ValueError:
        return None

    event_sec = event.timestamp // 1000000
    window_id = (event_sec // window_size_sec) * window_size_sec

    if detector_domain == DetectorDomain.RECON and event.event_type == EventType.CONNECTION:
        dst_port = event.dst_port
        if dst_port is not None:
            await state_adapter.add_tumbling_distinct(
                entity_type, entity_key, window_id, "dst_port", str(dst_port), ttl_seconds=window_size_sec*2
            )

        # Get count
        unique_ports = await state_adapter.count_tumbling_distinct(
            entity_type, entity_key, window_id, "dst_port"
        )

        envelope_args = await build_envelope(
            state_adapter, event, FeatureMechanism.WINDOWED,
            detector_domain, entity_type, entity_key,
            window_type=WindowType.TUMBLING,
            window_start=window_id * 1000000,
            window_end=(window_id + window_size_sec) * 1000000
        )
        payload = ReconFeaturePayload(unique_destination_ports=unique_ports)
        return ReconFeatureRecord(**envelope_args, payload=payload)

    return None

# --- M3.8 Session / Correlation Mechanism ---
async def process_correlation(
    state_adapter: FeatureStateAdapter,
    event: CanonicalEvent,
    detector_domain: DetectorDomain,
    entity_type: EntityType,
    correlation_ttl_sec: int
) -> Optional[FeatureRecord]:
    """
    Processes an event into a correlation feature record.
    Note: Current partial/complete handling is the minimum WP-D baseline.
    Final correlation timeout or late-amendment policies remain OPEN.
    """
    try:
        entity_key = build_entity_key(entity_type, event.src_ip, event.dst_ip, event.connection_id)
    except ValueError:
        return None

    # E.g. TLS/C2 connection <-> tls join
    if detector_domain == DetectorDomain.TLS_C2:
        fields_to_update = {}
        if event.event_type == EventType.CONNECTION:
            fields_to_update["conn_seen"] = "1"
        elif event.event_type == EventType.TLS:
            fields_to_update["tls_seen"] = "1"

        await state_adapter.set_correlation_state(event.connection_id, fields_to_update, ttl_seconds=correlation_ttl_sec)

        current_state = await state_adapter.get_correlation_state(event.connection_id)

        status = CorrelationStatus.PARTIAL
        if "conn_seen" in current_state and "tls_seen" in current_state:
            status = CorrelationStatus.COMPLETE

        envelope_args = await build_envelope(
            state_adapter, event, FeatureMechanism.CORRELATION,
            detector_domain, entity_type, entity_key
        )

        payload = TlsC2FeaturePayload(
            correlation_status=status
        )
        return TlsC2FeatureRecord(**envelope_args, payload=payload)

    return None
