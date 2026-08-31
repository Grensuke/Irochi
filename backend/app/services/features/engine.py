import logging
from typing import List, Optional
from pydantic import TypeAdapter

from app.services.streaming.consumer import ConsumerMessage
from app.schemas.canonical import CanonicalEvent, EventType
from app.schemas.features import FeatureRecord, DetectorDomain, EntityType
from app.services.features.state import FeatureStateAdapter
from app.services.features.mechanisms import (
    process_enrichment, process_sliding, process_tumbling, process_correlation
)

logger = logging.getLogger(__name__)

class FeatureEngine:
    def __init__(self, state_adapter: FeatureStateAdapter):
        self.state_adapter = state_adapter
        self._canonical_adapter = TypeAdapter(CanonicalEvent)

    def parse_canonical_event(self, message: ConsumerMessage) -> Optional[CanonicalEvent]:
        """Parses a raw dict into a CanonicalEvent Pydantic model."""
        try:
            # TypeAdapter handles the Union discriminator based on event_type
            return self._canonical_adapter.validate_python(message.payload)
        except Exception as e:
            logger.error(f"Failed to parse canonical event from partition {message.partition} offset {message.offset}: {e}")
            return None

    async def process(self, message: ConsumerMessage) -> List[FeatureRecord]:
        """
        Main processing loop boundary.
        Transforms a Redpanda ConsumerMessage into zero or more FeatureRecords.
        """
        event = self.parse_canonical_event(message)
        if not event:
            return []

        records = []

        # Route to mechanisms based on event_type and domains.
        # This acts as the reusable dispatcher.

        if event.event_type == EventType.DNS:
            dns_enrich = await process_enrichment(
                self.state_adapter, event, DetectorDomain.DNS, EntityType.SOURCE
            )
            if dns_enrich: records.append(dns_enrich)

            dns_sliding = await process_sliding(
                self.state_adapter, event, DetectorDomain.DNS, EntityType.SOURCE,
                bucket_width_sec=60, # DEVELOPMENT CONFIG ONLY: Open parameter
                window_size_sec=300  # DEVELOPMENT CONFIG ONLY: Open parameter
            )
            if dns_sliding: records.append(dns_sliding)

        elif event.event_type == EventType.TLS:
            tls_enrich = await process_enrichment(
                self.state_adapter, event, DetectorDomain.TLS_C2, EntityType.CONNECTION
            )
            if tls_enrich: records.append(tls_enrich)

            tls_corr = await process_correlation(
                self.state_adapter, event, DetectorDomain.TLS_C2, EntityType.CONNECTION,
                correlation_ttl_sec=300 # DEVELOPMENT CONFIG ONLY: Open parameter
            )
            if tls_corr: records.append(tls_corr)

        elif event.event_type == EventType.CONNECTION:
            recon_tumble = await process_tumbling(
                self.state_adapter, event, DetectorDomain.RECON, EntityType.SOURCE,
                window_size_sec=3600 # DEVELOPMENT CONFIG ONLY: Open parameter
            )
            if recon_tumble: records.append(recon_tumble)

            tls_corr_conn = await process_correlation(
                self.state_adapter, event, DetectorDomain.TLS_C2, EntityType.CONNECTION,
                correlation_ttl_sec=300 # DEVELOPMENT CONFIG ONLY: Open parameter
            )
            if tls_corr_conn: records.append(tls_corr_conn)

        return records
