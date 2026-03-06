"""Async web scraper client for public goszakup.gov.kz pages."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from nova.config import get_settings


DEFAULT_TIMEOUT = 30.0
SEARCH_PATH = "/ru/search/announce"
DETAIL_PATH_TEMPLATE = "/ru/announce/index/{tender_id}"

logger = logging.getLogger(__name__)


class GoszakupScraperError(RuntimeError):
    """Base exception for goszakup scraper failures."""


class GoszakupForbiddenError(GoszakupScraperError):
    """Raised when goszakup rejects access to a page."""


class GoszakupRateLimitError(GoszakupScraperError):
    """Raised when goszakup temporarily rate-limits the client."""


class GoszakupServerError(GoszakupScraperError):
    """Raised when goszakup returns a 5xx response."""


class GoszakupTransportError(GoszakupScraperError):
    """Raised when a network-level error prevents fetching a page."""


class GoszakupScraper:
    """Lazy async HTTP client for goszakup public HTML pages."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        user_agent: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.AsyncBaseTransport | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.goszakup_base_url).rstrip("/")
        self._user_agent = user_agent or settings.goszakup_user_agent
        self._timeout = timeout
        self._transport = transport
        self._client = client

    async def __aenter__(self) -> "GoszakupScraper":
        await self._get_client()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.aclose()

    @property
    def base_url(self) -> str:
        """Return the configured goszakup base URL."""
        return self._base_url

    @property
    def default_headers(self) -> dict[str, str]:
        """Return the default headers used for HTTP requests."""
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": self._user_agent,
        }

    async def aclose(self) -> None:
        """Close the underlying HTTP client if it was created lazily."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch_search_page(self, *, params: dict[str, Any] | None = None) -> str:
        """Fetch the tender search page HTML."""
        return await self._request_html(SEARCH_PATH, params=params)

    async def fetch_tender_page(
        self,
        tender_id: int,
        *,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Fetch a tender detail page HTML."""
        path = DETAIL_PATH_TEMPLATE.format(tender_id=tender_id)
        return await self._request_html(path, params=params)

    async def search_tenders(self, **_: Any) -> list[Any]:
        """Search mapping is implemented in later Step 2.1 substeps."""
        raise NotImplementedError("search_tenders is implemented after parser wiring")

    async def get_tender_details(self, tender_id: int) -> Any:
        """Detail mapping is implemented in later Step 2.1 substeps."""
        raise NotImplementedError(f"get_tender_details is not implemented for {tender_id}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=self.default_headers,
                timeout=self._timeout,
                transport=self._transport,
                follow_redirects=True,
            )
        return self._client

    async def _request_html(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> str:
        client = await self._get_client()
        logger.info("Fetching goszakup page %s", path)

        try:
            response = await client.get(path, params=params)
        except httpx.TransportError as exc:
            raise GoszakupTransportError(f"Failed to fetch goszakup page {path!r}") from exc

        self._raise_for_status(response)
        return response.text

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        status = response.status_code
        if status == 403:
            raise GoszakupForbiddenError("Goszakup returned 403 Forbidden")
        if status == 429:
            raise GoszakupRateLimitError("Goszakup returned 429 Too Many Requests")
        if status >= 500:
            raise GoszakupServerError(f"Goszakup returned server error {status}")
        response.raise_for_status()
