from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Awaitable, Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass
class RateLimitConfig:
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10


class InMemoryRateLimiter:
    """内存限流器（单进程部署用）。

    生产环境建议替换为 Redis 限流器。
    """

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._minute_buckets: dict[str, dict[float, int]] = defaultdict(dict)
        self._hour_buckets: dict[str, dict[float, int]] = defaultdict(dict)

    def _cleanup(self, buckets: dict[str, dict[float, int]], window: float) -> None:
        now = time.time()
        for key in list(buckets.keys()):
            buckets[key] = {t: c for t, c in buckets[key].items() if now - t < window}
            if not buckets[key]:
                del buckets[key]

    def check_and_increment(self, key: str) -> tuple[bool, dict[str, int]]:
        now = time.time()
        minute_window = 60.0
        hour_window = 3600.0

        self._cleanup(self._minute_buckets, minute_window)
        self._cleanup(self._hour_buckets, hour_window)

        minute_bucket = now // minute_window * minute_window
        hour_bucket = now // hour_window * hour_window

        minute_count = self._minute_buckets[key].get(minute_bucket, 0)
        hour_count = self._hour_buckets[key].get(hour_bucket, 0)

        if minute_count >= self.config.requests_per_minute:
            return False, {
                "minute_limit": self.config.requests_per_minute,
                "minute_remaining": 0,
                "hour_limit": self.config.requests_per_hour,
                "hour_remaining": max(0, self.config.requests_per_hour - hour_count),
            }

        if hour_count >= self.config.requests_per_hour:
            return False, {
                "minute_limit": self.config.requests_per_minute,
                "minute_remaining": max(0, self.config.requests_per_minute - minute_count),
                "hour_limit": self.config.requests_per_hour,
                "hour_remaining": 0,
            }

        self._minute_buckets[key][minute_bucket] = minute_count + 1
        self._hour_buckets[key][hour_bucket] = hour_count + 1

        return True, {
            "minute_limit": self.config.requests_per_minute,
            "minute_remaining": self.config.requests_per_minute - minute_count - 1,
            "hour_limit": self.config.requests_per_hour,
            "hour_remaining": self.config.requests_per_hour - hour_count - 1,
        }


_rate_limiter: InMemoryRateLimiter | None = None


def get_rate_limiter() -> InMemoryRateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter()
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """API 限流中间件。

    基于 IP 地址限流，支持每分钟和每小时两级限流。
    """

    def __init__(self, app, limiter: InMemoryRateLimiter | None = None):
        super().__init__(app)
        self.limiter = limiter or get_rate_limiter()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        key = f"ip:{client_ip}"

        allowed, info = self.limiter.check_and_increment(key)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "message": "请求过于频繁，请稍后再试",
                    **info,
                },
                headers={
                    "X-RateLimit-Limit": str(info["minute_limit"]),
                    "X-RateLimit-Remaining": str(info["minute_remaining"]),
                    "Retry-After": "60",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["minute_limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["minute_remaining"])
        return response
