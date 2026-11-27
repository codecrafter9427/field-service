"""Tiny in-process rate limiter (portfolio MVP — resets per process)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.api.errors import api_error
from starlette import status

_lock = threading.Lock()
_buckets: dict[str, deque[float]] = defaultdict(deque)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_rate_limit(key: str, *, limit: int, window_seconds: int = 60) -> None:
    """Raise 429 if `key` exceeded `limit` hits in the sliding window."""
    if limit <= 0:
        return
    now = time.monotonic()
    cutoff = now - window_seconds
    with _lock:
        bucket = _buckets[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            raise api_error(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "rate_limited",
                "Too many requests; try again shortly",
            )
        bucket.append(now)


def reset_rate_limits() -> None:
    """Test helper."""
    with _lock:
        _buckets.clear()
