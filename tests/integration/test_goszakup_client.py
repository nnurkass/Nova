"""Integration-style tests for the goszakup GraphQL client."""
from __future__ import annotations

import importlib
import sys

import httpx
import pytest

from nova.integrations.goszakup.client import GoszakupClient


def test_importing_goszakup_client_has_no_side_effects():
    sys.modules.pop("nova.integrations.goszakup.client", None)

    module = importlib.import_module("nova.integrations.goszakup.client")

    assert module.GoszakupClient is not None


@pytest.mark.asyncio
async def test_execute_query_returns_graphql_data():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer token-123"
        assert request.url == httpx.URL("https://example.test/graphql")
        assert request.method == "POST"
        assert request.read().decode("utf-8")
        return httpx.Response(
            200,
            json={
                "data": {
                    "announcements": {
                        "total": 1,
                    }
                }
            },
        )

    transport = httpx.MockTransport(handler)
    client = GoszakupClient(
        token="token-123",
        graphql_url="https://example.test/graphql",
        transport=transport,
    )

    result = await client.execute_query("query Test { announcements { total } }", {"limit": 1})

    assert result == {"announcements": {"total": 1}}
    await client.close()
