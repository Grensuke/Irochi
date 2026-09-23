"""
Sliding window rate limiter using Redis INCR + EXPIRE.
No third-party library — pure Redis implementation.
"""

from __future__ import annotations

import math
import time
from datetime import datetime, timezone

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.redis_client import get_redis_client

logger = structlog.get_logger(__name__)

# ── Rate limit configuration ────────────────────────────────────

ROUTE_LIMITS: dict[str, int] = {
    "/auth/login": 10,  # 10 requests per minute per IP
}
DEFAULT_LIMIT = 300  # 300 requests per minute per user_id (or IP)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP and per-user sliding window rate limiter using Redis.

    - POST /auth/login: 10 req/min per IP address
    - All other routes: 300 req/min per user_id (or per IP if unauthenticated)
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for health, metrics, and docs
        skip_paths = ("/health", "/metrics", "/docs", "/redoc", "/openapi.json")
        if request.url.path in skip_paths:
            return await call_next(request)

        # Skip WebSocket upgrades
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        try:
            redis = get_redis_client()
        except RuntimeError:
            # Redis not initialized yet — skip rate limiting
            return await call_next(request)

        # Determine identifier and limit
        path = request.url.path
        client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()

        if path in ROUTE_LIMITS:
            # Login: rate limit by IP
            identifier = client_ip
            limit = ROUTE_LIMITS[path]
            route_group = "login"
        else:
            # Try to get user_id from auth header for per-user limiting
            identifier = client_ip  # fallback
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                try:
                    from app.auth.utils import decode_token
                    token = auth_header[7:]
                    payload = decode_token(token)
                    identifier = payload.get("sub", client_ip)
                except Exception:
                    pass
            limit = DEFAULT_LIMIT
            route_group = "api"

        # Current minute bucket
        current_minute = int(time.time() // 60)
        key = f"ratelimit:{identifier}:{route_group}:{current_minute}"

        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 60)

            if count > limit:
                # Calculate retry-after
                seconds_into_minute = int(time.time() % 60)
                retry_after = 60 - seconds_into_minute

                logger.warning(
                    "rate_limit_exceeded",
                    identifier=identifier,
                    route_group=route_group,
                    count=count,
                    limit=limit,
                )

                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": retry_after,
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(current_minute * 60 + 60),
                        "Retry-After": str(retry_after),
                    },
                )

            response = await call_next(request)

            # Add rate limit headers
            remaining = max(0, limit - count)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(current_minute * 60 + 60)

            return response

        except Exception as exc:
            # If Redis fails, allow the request through
            logger.warning("rate_limit_redis_error", error=str(exc))
            return await call_next(request)
