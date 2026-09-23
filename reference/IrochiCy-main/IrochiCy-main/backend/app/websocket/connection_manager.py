"""
WebSocket connection manager for real-time alert broadcasting.
Keyed by user_id for targeted messaging support.
"""

from __future__ import annotations

import asyncio

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections keyed by user_id.
    Supports broadcast and per-user messaging.
    Allows multiple connections (tabs) per user.
    """

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    @property
    def connection_count(self) -> int:
        return sum(len(websockets) for websockets in self._connections.values())

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)
        logger.info(
            "ws_connected",
            user_id=user_id,
            total_connections=self.connection_count,
        )

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info(
            "ws_disconnected",
            user_id=user_id,
            total_connections=self.connection_count,
        )

    async def send_to_user(self, user_id: str, message: dict) -> None:
        """Send a JSON message to a specific user's connections."""
        websockets = self._connections.get(user_id, set())
        stale = set()
        for ws in websockets:
            try:
                await ws.send_json(message)
            except Exception:
                stale.add(ws)
        
        for ws in stale:
            self.disconnect(user_id, ws)

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to all connected clients."""
        tasks = []
        for websockets in self._connections.values():
            for ws in websockets:
                tasks.append(self._send_to_socket(ws, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_socket(self, websocket: WebSocket, message: dict) -> None:
        """Helper to send to a single socket and handle errors."""
        try:
            await websocket.send_json(message)
        except Exception:
            # We don't have the user_id here easily, 
            # so we let the higher-level logic handle cleanup or tolerate transient failures
            pass

    async def close_all(self, code: int = 1001) -> None:
        """Gracefully close all WebSocket connections."""
        for ws in list(self._connections.values()):
            try:
                await ws.close(code=code)
            except Exception:
                pass
        self._connections.clear()
        logger.info("ws_all_closed")


# Global singleton
manager = ConnectionManager()
