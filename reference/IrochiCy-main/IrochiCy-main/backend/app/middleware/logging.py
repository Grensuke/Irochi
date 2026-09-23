"""Structured request/response logging middleware using structlog."""

from __future__ import annotations

import time
import traceback
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("http")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request as structured JSON with:
    - request_id (UUID, attached to request.state)
    - method, path, status_code
    - duration_ms
    - user_agent, client IP
    Exceptions are caught, logged with traceback, then re-raised.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "http_request_error",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                error=str(exc),
                traceback=traceback.format_exc(),
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "http_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        response.headers["X-Request-ID"] = request_id
        return response
