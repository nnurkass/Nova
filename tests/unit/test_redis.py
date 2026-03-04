"""Unit tests for nova.config.redis — mock-based, no live Redis required."""
import json
from unittest.mock import MagicMock, patch
import redis as redis_lib
import pytest
import nova.config.redis as r_module
from nova.config.redis import check_connection, get_cache, set_cache, delete_cache


@pytest.fixture(autouse=True)
def reset_client():
    r_module._client = None
    yield
    r_module._client = None


def test_check_connection_success():
    mock = MagicMock()
    mock.ping.return_value = True
    with patch("nova.config.redis.get_redis_client", return_value=mock):
        assert check_connection() is True


def test_check_connection_failure():
    mock = MagicMock()
    mock.ping.side_effect = redis_lib.RedisError("timeout")
    with patch("nova.config.redis.get_redis_client", return_value=mock):
        assert check_connection() is False


def test_get_cache_hit():
    mock = MagicMock()
    mock.get.return_value = '{"x": 1}'
    with patch("nova.config.redis.get_redis_client", return_value=mock):
        assert get_cache("k") == {"x": 1}


def test_get_cache_miss():
    mock = MagicMock()
    mock.get.return_value = None
    with patch("nova.config.redis.get_redis_client", return_value=mock):
        assert get_cache("k") is None


def test_set_cache_calls_setex():
    mock = MagicMock()
    with patch("nova.config.redis.get_redis_client", return_value=mock):
        result = set_cache("k", {"a": 1}, ttl=300)
    assert result is True
    mock.setex.assert_called_once_with("k", 300, json.dumps({"a": 1}))


def test_set_cache_redis_error_returns_false():
    mock = MagicMock()
    mock.setex.side_effect = redis_lib.RedisError("refused")
    with patch("nova.config.redis.get_redis_client", return_value=mock):
        assert set_cache("k", "v") is False


def test_delete_cache():
    mock = MagicMock()
    with patch("nova.config.redis.get_redis_client", return_value=mock):
        result = delete_cache("k")
    assert result is True
    mock.delete.assert_called_once_with("k")
