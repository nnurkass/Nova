"""Redis helpers for cache operations and connectivity checks."""
from __future__ import annotations

import json
from typing import Any

from redis import Redis


DEFAULT_CACHE_TTL = 1800

_redis_client: Redis | None = None


def get_redis_client(url: str | None = None, **kwargs: Any) -> Redis:
    """Return a Redis client, using a module-level singleton by default."""
    if url is not None:
        return Redis.from_url(url, decode_responses=True, **kwargs)

    global _redis_client
    if _redis_client is None:
        from nova.config.settings import settings

        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True, **kwargs)
    return _redis_client


def check_redis_connection(client: Redis | None = None) -> bool:
    """Ping Redis and return whether the connection is healthy."""
    redis_client = client or get_redis_client()
    try:
        return bool(redis_client.ping())
    except Exception:
        return False


def get_cache(key: str, default: Any = None, client: Redis | None = None) -> Any:
    """Return a cached JSON value or the provided default."""
    redis_client = client or get_redis_client()
    payload = redis_client.get(key)
    if payload is None:
        return default
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload


def set_cache(
    key: str,
    value: Any,
    ttl: int = DEFAULT_CACHE_TTL,
    client: Redis | None = None,
) -> bool:
    """Serialize a JSON-compatible value and store it in Redis."""
    redis_client = client or get_redis_client()
    payload = json.dumps(value)

    if ttl > 0:
        return bool(redis_client.setex(key, ttl, payload))
    return bool(redis_client.set(key, payload))


def delete_cache(key: str, client: Redis | None = None) -> bool:
    """Delete a cached key and report whether something was removed."""
    redis_client = client or get_redis_client()
    return bool(redis_client.delete(key))
