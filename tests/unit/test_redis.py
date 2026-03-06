"""Unit tests for Redis cache helpers."""
from __future__ import annotations

import pytest
from redis.exceptions import RedisError

from nova.config.redis import (
    DEFAULT_CACHE_TTL,
    check_redis_connection,
    delete_cache,
    get_cache,
    get_redis_client,
    reset_redis_client,
    set_cache,
)


class FakeRedis:
    def __init__(self):
        self.storage: dict[str, str] = {}
        self.last_ttl: int | None = None
        self.ping_result = True
        self.raise_on_ping = False
        self.raise_on_get = False
        self.raise_on_set = False
        self.raise_on_delete = False
        self.closed = False

    def ping(self) -> bool:
        if self.raise_on_ping:
            raise RedisError("ping failed")
        return self.ping_result

    def get(self, key: str) -> str | None:
        if self.raise_on_get:
            raise RedisError("get failed")
        return self.storage.get(key)

    def set(self, key: str, value: str) -> bool:
        if self.raise_on_set:
            raise RedisError("set failed")
        self.storage[key] = value
        self.last_ttl = None
        return True

    def setex(self, key: str, ttl: int, value: str) -> bool:
        if self.raise_on_set:
            raise RedisError("set failed")
        self.storage[key] = value
        self.last_ttl = ttl
        return True

    def delete(self, key: str) -> int:
        if self.raise_on_delete:
            raise RedisError("delete failed")
        return int(self.storage.pop(key, None) is not None)

    def close(self) -> None:
        self.closed = True


class TestRedisHelpers:
    def test_get_redis_client_uses_singleton(self, monkeypatch):
        fake_one = FakeRedis()
        fake_two = FakeRedis()
        calls: list[tuple[str, bool]] = []
        fake_settings = type("FakeSettings", (), {"redis_url": "redis://cache:6379/7"})()

        def fake_from_url(url: str, decode_responses: bool = False, **kwargs):
            calls.append((url, decode_responses))
            return fake_one if len(calls) == 1 else fake_two

        monkeypatch.setattr("redis.Redis.from_url", fake_from_url)
        monkeypatch.setattr("nova.config.redis.get_settings", lambda: fake_settings)
        reset_redis_client()

        first = get_redis_client()
        second = get_redis_client()

        assert first is fake_one
        assert second is fake_one
        assert calls == [("redis://cache:6379/7", True)]

    def test_get_redis_client_recreates_default_client_when_url_changes(self, monkeypatch):
        fake_one = FakeRedis()
        fake_two = FakeRedis()
        urls = ["redis://cache:6379/1", "redis://cache:6379/2"]
        fake_settings = type("FakeSettings", (), {"redis_url": urls[0]})()

        def fake_from_url(url: str, decode_responses: bool = False, **kwargs):
            return fake_one if url == urls[0] else fake_two

        monkeypatch.setattr("redis.Redis.from_url", fake_from_url)
        monkeypatch.setattr("nova.config.redis.get_settings", lambda: fake_settings)
        reset_redis_client()

        first = get_redis_client()
        fake_settings.redis_url = urls[1]
        second = get_redis_client()

        assert first is fake_one
        assert second is fake_two

    def test_get_cache_returns_default_on_miss(self):
        fake = FakeRedis()
        assert get_cache("missing", default={"ok": False}, client=fake) == {"ok": False}

    def test_set_cache_and_get_cache_roundtrip_json(self):
        fake = FakeRedis()
        payload = {"value": 42, "items": ["a", "b"]}

        assert set_cache("example", payload, client=fake) is True
        assert fake.last_ttl == DEFAULT_CACHE_TTL
        assert get_cache("example", client=fake) == payload

    def test_set_cache_uses_plain_set_when_ttl_is_none(self):
        fake = FakeRedis()

        assert set_cache("example", ["a", "b"], ttl=None, client=fake) is True
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

    def test_get_cache_returns_default_on_redis_error(self):
        fake = FakeRedis()
        fake.raise_on_get = True

        assert get_cache("missing", default="fallback", client=fake) == "fallback"

    def test_get_cache_deletes_corrupt_json_and_returns_default(self):
        fake = FakeRedis()
        fake.storage["broken"] = "{not-json"

        assert get_cache("broken", default="fallback", client=fake) == "fallback"
        assert "broken" not in fake.storage

    def test_set_cache_returns_false_on_redis_error(self):
        fake = FakeRedis()
        fake.raise_on_set = True

        assert set_cache("example", {"ok": True}, client=fake) is False

    def test_delete_cache_returns_false_on_redis_error(self):
        fake = FakeRedis()
        fake.raise_on_delete = True

        assert delete_cache("example", client=fake) is False

    def test_set_cache_rejects_non_positive_ttl(self):
        fake = FakeRedis()

        with pytest.raises(ValueError):
            set_cache("example", ["a", "b"], ttl=0, client=fake)

        with pytest.raises(ValueError):
            set_cache("example", ["a", "b"], ttl=-1, client=fake)

    def test_set_cache_raises_for_non_serializable_values(self):
        fake = FakeRedis()

        with pytest.raises(TypeError):
            set_cache("bad", {1, 2, 3}, client=fake)
