from app.schemas.features import EntityType

# DEVELOPMENT CONFIG: The exact serialization format and delimiter remain OPEN.
# The serialization used to store state in Redis is NOT an architectural rule.
# The logical identity (src_ip, dst_ip) is locked, but how it is serialized here is an implementation choice.
_DELIMITER = "|"

def build_pair_key(src_ip: str, dst_ip: str) -> str:
    """Builds a directional pair key (src_ip, dst_ip)."""
    return f"{src_ip}{_DELIMITER}{dst_ip}"

def build_entity_key(entity_type: EntityType, src_ip: str, dst_ip: str, connection_id: str) -> str:
    """Extracts/builds the correct entity key based on the type and available data."""
    if entity_type == EntityType.SOURCE:
        if not src_ip:
            raise ValueError("src_ip required for SOURCE entity")
        return src_ip
    elif entity_type == EntityType.DESTINATION:
        if not dst_ip:
            raise ValueError("dst_ip required for DESTINATION entity")
        return dst_ip
    elif entity_type == EntityType.PAIR:
        if not src_ip or not dst_ip:
            raise ValueError("src_ip and dst_ip required for PAIR entity")
        return build_pair_key(src_ip, dst_ip)
    elif entity_type == EntityType.CONNECTION:
        if not connection_id:
            raise ValueError("connection_id required for CONNECTION entity")
        return connection_id
    else:
        raise ValueError(f"Unknown entity type: {entity_type}")

def parse_pair_key(pair_key: str) -> tuple[str, str]:
    """Parses a pair key back into (src_ip, dst_ip)."""
    parts = pair_key.split(_DELIMITER)
    if len(parts) != 2:
        raise ValueError(f"Invalid pair key: {pair_key}")
    return parts[0], parts[1]
