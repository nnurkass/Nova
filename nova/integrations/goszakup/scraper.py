"""Async web scraper client for public goszakup.gov.kz pages."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import httpx

from nova.config import get_cache, get_settings, set_cache
from nova.config.redis import DEFAULT_CACHE_TTL
from nova.integrations.goszakup.models import Tender, TenderSearchFilter
from nova.integrations.goszakup.parsers import parse_search_results, parse_tender_detail


DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRY_DELAYS = (1.0, 3.0, 9.0)
SEARCH_PATH = "/ru/search/announce"
DETAIL_PATH_TEMPLATE = "/ru/announce/index/{tender_id}"
CACHE_PREFIX = "goszakup"

REGION_ALIASES = {
    "алматы": "Алматы",
    "город алматы": "Алматы",
    "almaty": "Алматы",
    "астана": "Астана",
    "город астана": "Астана",
    "astana": "Астана",
}

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
        cache_ttl: int = DEFAULT_CACHE_TTL,
        retry_delays: tuple[float, ...] = DEFAULT_RETRY_DELAYS,
        sleep_func: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.goszakup_base_url).rstrip("/")
        self._user_agent = user_agent or settings.goszakup_user_agent
        self._timeout = timeout
        self._transport = transport
        self._client = client
        self._cache_ttl = cache_ttl
        self._retry_delays = retry_delays
        self._sleep = sleep_func or asyncio.sleep

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

    async def search_tenders(
        self,
        *,
        region: str | None = None,
        work_type: str | None = None,
        budget_min: float | None = None,
        budget_max: float | None = None,
        deadline_from: datetime | str | None = None,
        limit: int = 10,
    ) -> list[Tender]:
        """Search public tender listing pages and return parsed tenders."""
        search_filter = self._build_search_filter(
            region=region,
            work_type=work_type,
            budget_min=budget_min,
            budget_max=budget_max,
            deadline_from=deadline_from,
            limit=limit,
        )
        if search_filter.limit <= 0:
            return []

        tenders: list[Tender] = []
        seen_tender_ids: set[int] = set()
        page = 1

        while len(tenders) < search_filter.limit:
            page_results, source = await self._load_search_page(search_filter, page=page)
            logger.info(
                "Loaded goszakup search page %s from %s with %s results",
                page,
                source,
                len(page_results),
            )
            if not page_results:
                break

            fresh_results = 0
            for tender in page_results:
                if tender.id in seen_tender_ids:
                    continue
                tenders.append(tender)
                seen_tender_ids.add(tender.id)
                fresh_results += 1
                if len(tenders) >= search_filter.limit:
                    break

            if fresh_results == 0:
                break
            page += 1

        return tenders[: search_filter.limit]

    async def get_tender_details(self, tender_id: int) -> Tender:
        """Load and parse a tender detail page."""
        parsed_key = self._cache_key("detail:parsed", {"tender_id": tender_id})
        cached_payload = self._safe_get_cache(parsed_key)
        if isinstance(cached_payload, dict):
            logger.info("Loaded goszakup tender %s details from parsed cache", tender_id)
            return Tender.model_validate(cached_payload)

        path = DETAIL_PATH_TEMPLATE.format(tender_id=tender_id)
        raw_key = self._cache_key("detail:html", {"tender_id": tender_id})
        html, source = await self._load_html(path=path, params=None, cache_key=raw_key)
        detail = parse_tender_detail(html, tender_id=tender_id, base_url=self._base_url)
        if detail.detail_url is None:
            detail = detail.model_copy(update={"detail_url": urljoin(f"{self._base_url}/", path.lstrip("/"))})
        self._safe_set_cache(parsed_key, detail.model_dump(mode="json"))
        logger.info("Loaded goszakup tender %s detail from %s", tender_id, source)
        return detail

    async def download_document(self, document_url: str) -> bytes:
        """Download a tender attachment using the scraper retry policy."""
        return await self._request_bytes(document_url)

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
        response = await self._request(path, params=params)
        return response.text

    async def _request_bytes(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> bytes:
        response = await self._request(path, params=params)
        return response.content

    async def _request(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        client = await self._get_client()
        total_attempts = len(self._retry_delays) + 1

        for attempt in range(1, total_attempts + 1):
            logger.info("Fetching goszakup page %s (attempt %s/%s)", path, attempt, total_attempts)
            try:
                response = await client.get(path, params=params)
                self._raise_for_status(response)
                return response
            except GoszakupForbiddenError:
                logger.warning("Goszakup denied access to %s on attempt %s", path, attempt)
                raise
            except (GoszakupRateLimitError, GoszakupServerError) as exc:
                if attempt >= total_attempts:
                    raise
                delay = self._retry_delays[attempt - 1]
                logger.warning(
                    "Transient goszakup HTTP error on %s attempt %s/%s: %s; retrying in %.1fs",
                    path,
                    attempt,
                    total_attempts,
                    exc,
                    delay,
                )
                await self._sleep(delay)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                transport_error = GoszakupTransportError(f"Failed to fetch goszakup page {path!r}")
                if attempt >= total_attempts:
                    raise transport_error from exc
                delay = self._retry_delays[attempt - 1]
                logger.warning(
                    "Transient goszakup transport error on %s attempt %s/%s: %s; retrying in %.1fs",
                    path,
                    attempt,
                    total_attempts,
                    exc,
                    delay,
                )
                await self._sleep(delay)

        raise GoszakupTransportError(f"Failed to fetch goszakup page {path!r}")

    async def _load_search_page(
        self,
        search_filter: TenderSearchFilter,
        *,
        page: int,
    ) -> tuple[list[Tender], str]:
        payload = search_filter.model_dump(mode="json", exclude_none=True)
        payload["page"] = page

        parsed_key = self._cache_key("search:parsed", payload)
        cached_parsed = self._safe_get_cache(parsed_key)
        if isinstance(cached_parsed, list):
            return [Tender.model_validate(item) for item in cached_parsed], "cache"

        params = self._build_search_params(search_filter, page=page)
        raw_key = self._cache_key("search:html", payload)
        html, source = await self._load_html(path=SEARCH_PATH, params=params, cache_key=raw_key)
        tenders = parse_search_results(html, base_url=self._base_url)
        self._safe_set_cache(
            parsed_key,
            [tender.model_dump(mode="json") for tender in tenders],
        )
        return tenders, source

    async def _load_html(
        self,
        *,
        path: str,
        params: dict[str, Any] | None,
        cache_key: str,
    ) -> tuple[str, str]:
        cached_html = self._safe_get_cache(cache_key)
        if isinstance(cached_html, str):
            logger.info("Loaded goszakup page %s from raw HTML cache", path)
            return cached_html, "cache"

        html = await self._request_html(path, params=params)
        self._safe_set_cache(cache_key, html)
        return html, "network"

    def _build_search_filter(
        self,
        *,
        region: str | None = None,
        work_type: str | None = None,
        budget_min: float | None = None,
        budget_max: float | None = None,
        deadline_from: datetime | str | None = None,
        limit: int = 10,
    ) -> TenderSearchFilter:
        if isinstance(deadline_from, str):
            try:
                deadline_from = datetime.fromisoformat(deadline_from)
            except ValueError:
                deadline_from = datetime.strptime(deadline_from, "%Y-%m-%d")
        return TenderSearchFilter(
            region=self._normalize_region(region),
            work_type=self._normalize_text(work_type),
            budget_min=budget_min,
            budget_max=budget_max,
            deadline_from=deadline_from,
            limit=limit,
        )

    def _build_search_params(
        self,
        search_filter: TenderSearchFilter,
        *,
        page: int,
    ) -> dict[str, str]:
        params: dict[str, str] = {
            "page": str(page),
            "count_record": str(search_filter.limit),
        }
        if search_filter.region:
            params["region"] = search_filter.region
        if search_filter.work_type:
            params["work_type"] = search_filter.work_type
        if search_filter.budget_min is not None:
            params["budget_min"] = self._float_to_string(search_filter.budget_min)
        if search_filter.budget_max is not None:
            params["budget_max"] = self._float_to_string(search_filter.budget_max)
        if search_filter.deadline_from is not None:
            params["deadline_from"] = search_filter.deadline_from.isoformat()
        return params

    def _cache_key(self, namespace: str, payload: dict[str, Any]) -> str:
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return f"{CACHE_PREFIX}:{namespace}:{digest}"

    def _safe_get_cache(self, key: str) -> Any:
        try:
            return get_cache(key)
        except Exception:
            logger.warning("Failed to read goszakup cache key %s", key, exc_info=True)
            return None

    def _safe_set_cache(self, key: str, value: Any) -> None:
        try:
            if not set_cache(key, value, ttl=self._cache_ttl):
                logger.warning("Goszakup cache set returned False for key %s", key)
        except Exception:
            logger.warning("Failed to write goszakup cache key %s", key, exc_info=True)

    @staticmethod
    def _normalize_region(region: str | None) -> str | None:
        normalized = GoszakupScraper._normalize_text(region)
        if normalized is None:
            return None
        return REGION_ALIASES.get(normalized.lower(), normalized)

    @staticmethod
    def _normalize_text(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None

    @staticmethod
    def _float_to_string(value: float) -> str:
        return f"{value:.2f}".rstrip("0").rstrip(".")

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        status = response.status_code
        if status == 403:
            raise GoszakupForbiddenError("Goszakup returned 403 Forbidden")
        if status == 429:
            raise GoszakupRateLimitError("Goszakup returned 429 Too Many Requests")
        if status >= 500:
            raise GoszakupServerError(f"Goszakup returned server error {status}")
        if status >= 400:
            raise GoszakupScraperError(f"Goszakup returned HTTP {status}")
