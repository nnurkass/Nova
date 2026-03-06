"""Unit tests for Redis cache helpers."""
from __future__ import annotations

import pytest

from nova.config.redis import (
    DEFAULT_CACHE_TTL,
    check_redis_connection,
    delete_cache,
    get_cache,
    get_redis_client,
    set_cache,
)


class FakeRedis:
    def __init__(self):
        self.storage: dict[str, str] = {}
        self.last_ttl: int | None = None
        self.ping_result = True
        self.raise_on_ping = False

    def ping(self) -> bool:
        if self.raise_on_ping:
            raise RuntimeError("ping failed")
        return self.ping_result

    def get(self, key: str) -> str | None:
        return self.storage.get(key)

    def set(self, key: str, value: str) -> bool:
        self.storage[key] = value
        self.last_ttl = None
        return True

    def setex(self, key: str, ttl: int, value: str) -> bool:
        self.storage[key] = value
        self.last_ttl = ttl
        return True

    def delete(self, key: str) -> int:
        return int(self.storage.pop(key, None) is not None)


class TestRedisHelpers:
    def test_get_redis_client_uses_singleton(self, monkeypatch):
        fake = FakeRedis()
        calls: list[tuple[str, bool]] = []

        def fake_from_url(url: str, decode_responses: bool = False, **kwargs):
            calls.append((url, decode_responses))
            return fake

        monkeypatch.setattr("redis.Redis.from_url", fake_from_url)
        monkeypatch.setattr("nova.config.redis._redis_client", None)
        from nova.config.settings import settings

        monkeypatch.setattr(settings, "redis_url", "redis://cache:6379/7")

        first = get_redis_client()
        second = get_redis_client()

        assert first is fake
        assert second is fake
        assert calls == [("redis://cache:6379/7", True)]

    def test_get_cache_returns_default_on_miss(self):
        fake = FakeRedis()
        assert get_cache("missing", default={"ok": False}, client=fake) == {"ok": False}

    def test_set_cache_and_get_cache_roundtrip_json(self):
        fake = FakeRedis()
        payload = {"value": 42, "items": ["a", "b"]}

        assert set_cache("example", payload, client=fake) is True
        assert fake.last_ttl == DEFAULT_CACHE_TTL
        assert get_cache("example", client=fake) == payload

    def test_set_cache_uses_plain_set_when_ttl_is_zero(self):
        fake = FakeRedis()

        assert set_cache("example", ["a", "b"], ttl=0, client=fake) is True
        assert fake.last_ttl is None

    def test_delete_cache_reports_existing_keys(self):
        fake = FakeRedis()
        fake.storage["example"] = '"exists"'

        assert delete_cache("example", client=fake) is True
        assert delete_cache("example", client=fake) is False

    def test_check_redis_connection_returns_false_on_ping_error(self):
        fake = FakeRedis()
        fake.raise_on_ping = True

        assert check_redis_connection(client=fake) is False

    def test_set_cache_raises_for_non_serializable_values(self):
        fake = FakeRedis()

        with pytest.raises(TypeError):
            set_cache("bad", {1, 2, 3}, client=fake)
