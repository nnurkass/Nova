"""Redis helpers for cache operations and connectivity checks."""
from __future__ import annotations

import json
import logging
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from nova.config.settings import get_settings

DEFAULT_CACHE_TTL = 1800

logger = logging.getLogger(__name__)
_redis_client: Redis | None = None
_redis_client_url: str | None = None


def get_redis_client(url: str | None = None, **kwargs: Any) -> Redis:
    """Return a Redis client, reusing only the default client."""
    resolved_url = url or get_settings().redis_url
    if url is not None or kwargs:
        return Redis.from_url(resolved_url, decode_responses=True, **kwargs)

    global _redis_client, _redis_client_url
    if _redis_client is None or _redis_client_url != resolved_url:
        _redis_client = Redis.from_url(resolved_url, decode_responses=True)
        _redis_client_url = resolved_url
    return _redis_client


def reset_redis_client() -> None:
    """Close and clear the cached default Redis client."""
    global _redis_client, _redis_client_url
    if _redis_client is not None and hasattr(_redis_client, "close"):
        _redis_client.close()
    _redis_client = None
    _redis_client_url = None


def check_redis_connection(client: Redis | None = None) -> bool:
    """Ping Redis and return whether the connection is healthy."""
    redis_client = client or get_redis_client()
    try:
        return bool(redis_client.ping())
    except RedisError:
        return False


def get_cache(key: str, default: Any = None, client: Redis | None = None) -> Any:
    """Return a cached JSON value or the provided default."""
    redis_client = client or get_redis_client()
    try:
        payload = redis_client.get(key)
    except RedisError:
        logger.warning("Redis get failed for key %s", key, exc_info=True)
        return default

    if payload is None:
        return default
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON payload in Redis for key %s", key)
        try:
            redis_client.delete(key)
        except RedisError:
            logger.warning("Redis delete failed for corrupt key %s", key, exc_info=True)
        return default


def set_cache(
    key: str,
    value: Any,
    ttl: int | None = DEFAULT_CACHE_TTL,
    client: Redis | None = None,
) -> bool:
    """Serialize a JSON-compatible value and store it in Redis."""
    redis_client = client or get_redis_client()
    payload = json.dumps(value)
    if ttl is not None and ttl <= 0:
        raise ValueError("ttl must be a positive integer or None")

    try:
        if ttl is None:
            return bool(redis_client.set(key, payload))
        return bool(redis_client.setex(key, ttl, payload))
    except RedisError:
        logger.warning("Redis set failed for key %s", key, exc_info=True)
        return False


def delete_cache(key: str, client: Redis | None = None) -> bool:
    """Delete a cached key and report whether something was removed."""
    redis_client = client or get_redis_client()
    try:
        return bool(redis_client.delete(key))
    except RedisError:
        logger.warning("Redis delete failed for key %s", key, exc_info=True)
        return False
