"""Redis client and cache helpers. Implemented in Step 1.5."""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis

from nova.config.settings import settings

logger = logging.getLogger(__name__)
_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def check_connection() -> bool:
    try:
        get_redis_client().ping()
        return True
    except redis.RedisError as e:
        logger.warning("Redis connection failed: %s", e)
        return False


def get_cache(key: str) -> Optional[Any]:
    try:
        value = get_redis_client().get(key)
        return json.loads(value) if value is not None else None
    except redis.RedisError as e:
        logger.warning("Redis GET failed for key %r: %s", key, e)
        return None


def set_cache(key: str, value: Any, ttl: int = 1800) -> bool:
    try:
        get_redis_client().setex(key, ttl, json.dumps(value))
        return True
    except redis.RedisError as e:
        logger.warning("Redis SET failed for key %r: %s", key, e)
        return False


def delete_cache(key: str) -> bool:
    try:
        get_redis_client().delete(key)
        return True
    except redis.RedisError as e:
        logger.warning("Redis DELETE failed for key %r: %s", key, e)
        return False
