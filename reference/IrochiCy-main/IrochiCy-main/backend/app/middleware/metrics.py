"""Prometheus metrics middleware and endpoint."""

from __future__ import annotations

import time

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# ── Metrics ──────────────────────────────────────────────────────

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path_template", "status_code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path_template"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

WEBSOCKET_CONNECTIONS = Gauge(
    "websocket_connections_active",
    "Currently active WebSocket connections",
)

ALERTS_CREATED = Counter(
    "alerts_created_total",
    "Total alerts created by the alert engine",
    ["threat_type", "severity"],
)

ALERT_ENGINE_DURATION = Histogram(
    "alert_engine_duration_seconds",
    "Alert engine processing duration in seconds",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect Prometheus metrics for every HTTP request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        duration = time.perf_counter() - start

        # Use route path template for cardinality control
        path_template = request.url.path
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path"):
                path_template = route.path

        REQUEST_COUNT.labels(
            method=request.method,
            path_template=path_template,
            status_code=response.status_code,
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            path_template=path_template,
        ).observe(duration)

        return response


def metrics_endpoint() -> Response:
    """Return Prometheus metrics in the exposition format."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
