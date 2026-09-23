"""NetFlow/IPFIX reader — Stub for future implementation.

This module will parse NetFlow v5/v9 and IPFIX records into canonical events.
Currently not implemented; Zeek is the primary sensor for Phase 3.
"""

from __future__ import annotations

from typing import Iterator


class NetFlowReader:
    """Stub reader for NetFlow/IPFIX records.

    Raises NotImplementedError — implement in a future phase when
    NetFlow collectors are added to the pipeline.
    """

    def __init__(self, path: str) -> None:
        raise NotImplementedError(
            "NetFlow reader is not yet implemented. "
            "Use ZeekLogReader for Phase 3."
        )

    def __iter__(self) -> Iterator[dict]:
        raise NotImplementedError
