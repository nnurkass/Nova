"""Async GraphQL client for goszakup.gov.kz."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from nova.config import get_settings


logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 30.0


class GoszakupClientError(RuntimeError):
    """Base exception for goszakup client failures."""


class GoszakupUnauthorizedError(GoszakupClientError):
    """Raised when the goszakup API rejects the access token."""


class GoszakupRateLimitError(GoszakupClientError):
    """Raised when the goszakup API rate-limits the client."""


class GoszakupServerError(GoszakupClientError):
    """Raised when the goszakup API returns a 5xx response."""


class GoszakupGraphQLError(GoszakupClientError):
    """Raised when the GraphQL payload contains errors."""


class GoszakupClient:
    """Lazy async client for goszakup GraphQL requests."""

    def __init__(
        self,
        *,
        token: str | None = None,
        graphql_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = get_settings()
        self._token = token or settings.goszakup_token.get_secret_value()
        self._graphql_url = graphql_url or settings.goszakup_graphql_url
        self._timeout = timeout
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "GoszakupClient":
        await self._get_client()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    @property
    def graphql_url(self) -> str:
        return self._graphql_url

    async def close(self) -> None:
        """Close the underlying HTTP client if it was created."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=self._timeout,
                transport=self._transport,
            )
        return self._client

    async def execute_query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a raw GraphQL request and return the `data` payload."""
        client = await self._get_client()
        payload = {
            "query": query,
            "variables": variables or {},
        }
        logger.debug("Executing goszakup GraphQL query", extra={"variables": payload["variables"]})

        response = await client.post(self._graphql_url, json=payload)
        self._raise_for_status(response)

        body = response.json()
        errors = body.get("errors") or []
        if errors:
            raise GoszakupGraphQLError(str(errors[0]))

        data = body.get("data")
        if not isinstance(data, dict):
            raise GoszakupClientError("Goszakup response does not contain a GraphQL data object")
        return data

    async def search_tenders(
        self,
        *,
        region: str | None = None,
        work_type: str | None = None,
        budget_min: float | None = None,
        budget_max: float | None = None,
        deadline_from: Any | None = None,
        limit: int = 10,
    ) -> list[Any]:
        """Search implementation is added in the next step."""
        raise NotImplementedError("search_tenders mapping is implemented in Step 2.1.4")

    async def get_tender_details(self, tender_id: int) -> Any:
        """Detail mapping is added in the next step."""
        raise NotImplementedError("get_tender_details mapping is implemented in Step 2.1.4")

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        status = response.status_code
        if status == 401:
            raise GoszakupUnauthorizedError("Goszakup API returned 401 Unauthorized")
        if status == 429:
            raise GoszakupRateLimitError("Goszakup API returned 429 Too Many Requests")
        if status >= 500:
            raise GoszakupServerError(f"Goszakup API returned {status}")
        response.raise_for_status()
