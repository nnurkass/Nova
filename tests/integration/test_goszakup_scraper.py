"""Integration tests for the goszakup HTML scraper."""
from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest

from nova.integrations.goszakup.parsers import parse_search_results, parse_tender_detail
from nova.integrations.goszakup.scraper import (
    SEARCH_PATH,
    DETAIL_PATH_TEMPLATE,
    GoszakupForbiddenError,
    GoszakupScraper,
)


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "goszakup"
SEARCH_HTML = (FIXTURES_DIR / "search_results.html").read_text(encoding="utf-8")
DETAIL_HTML = (FIXTURES_DIR / "tender_detail.html").read_text(encoding="utf-8")


class MemoryCache:
    def __init__(self) -> None:
        self.storage: dict[str, object] = {}

    def get(self, key: str) -> object | None:
        return self.storage.get(key)

    def set(self, key: str, value: object, ttl: int | None = None) -> bool:
        self.storage[key] = value
        return True


def make_transport(
    responses: list[httpx.Response] | None = None,
    *,
    search_html: str = SEARCH_HTML,
    detail_html: str = DETAIL_HTML,
    calls: list[str] | None = None,
) -> httpx.MockTransport:
    queue = list(responses or [])

    async def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(f"{request.method} {request.url}")
        if queue:
            return queue.pop(0)
        if request.url.path == SEARCH_PATH:
            return httpx.Response(200, text=search_html)
        if request.url.path == DETAIL_PATH_TEMPLATE.format(tender_id=1001):
            return httpx.Response(200, text=detail_html)
        return httpx.Response(404, text="not found")

    return httpx.MockTransport(handler)


def patch_cache(monkeypatch: pytest.MonkeyPatch, cache: MemoryCache) -> None:
    monkeypatch.setattr("nova.integrations.goszakup.scraper.get_cache", cache.get)
    monkeypatch.setattr("nova.integrations.goszakup.scraper.set_cache", cache.set)


def test_parse_search_results_fixture():
    tenders = parse_search_results(SEARCH_HTML, base_url="https://goszakup.gov.kz")

    assert len(tenders) == 2
    assert tenders[0].id == 1001
    assert tenders[0].number == "АНО-2026-001"
    assert tenders[0].total_sum == 250000000.0
    assert tenders[0].detail_url == "https://goszakup.gov.kz/ru/announce/index/1001"
    assert tenders[0].status_name_ru == "Опубликовано"


def test_parse_tender_detail_fixture():
    tender = parse_tender_detail(DETAIL_HTML, tender_id=1001, base_url="https://goszakup.gov.kz")

    assert tender.id == 1001
    assert tender.customer_name_ru == 'ГУ "Отдел образования"'
    assert len(tender.lots) == 2
    assert tender.lots[0].name_ru == "Строительно-монтажные работы"
    assert tender.technical_specification is not None
    assert len(tender.documents) == 2
    assert tender.documents[0].url == "https://goszakup.gov.kz/storage/docs/specification.pdf"


@pytest.mark.asyncio
async def test_search_tenders_returns_models_and_uses_cache(monkeypatch: pytest.MonkeyPatch):
    cache = MemoryCache()
    patch_cache(monkeypatch, cache)
    calls: list[str] = []
    scraper = GoszakupScraper(transport=make_transport(calls=calls))

    first = await scraper.search_tenders(region="Алматы", limit=2)
    second = await scraper.search_tenders(region="Алматы", limit=2)

    assert [tender.id for tender in first] == [1001, 1002]
    assert [tender.id for tender in second] == [1001, 1002]
    assert len(calls) == 1
    await scraper.aclose()


@pytest.mark.asyncio
async def test_get_tender_details_returns_detail_model_and_uses_cache(monkeypatch: pytest.MonkeyPatch):
    cache = MemoryCache()
    patch_cache(monkeypatch, cache)
    calls: list[str] = []
    scraper = GoszakupScraper(transport=make_transport(calls=calls))

    first = await scraper.get_tender_details(1001)
    second = await scraper.get_tender_details(1001)

    assert first.id == 1001
    assert second.documents[1].name == "Смета"
    assert len(calls) == 1
    await scraper.aclose()


@pytest.mark.asyncio
async def test_search_tenders_retries_on_rate_limit(monkeypatch: pytest.MonkeyPatch):
    cache = MemoryCache()
    patch_cache(monkeypatch, cache)
    delays: list[float] = []
    calls: list[str] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    transport = make_transport(
        responses=[
            httpx.Response(429, text="rate limit"),
            httpx.Response(200, text=SEARCH_HTML),
        ],
        calls=calls,
    )
    scraper = GoszakupScraper(transport=transport, sleep_func=fake_sleep)

    tenders = await scraper.search_tenders(region="Алматы", limit=2)

    assert [tender.id for tender in tenders] == [1001, 1002]
    assert delays == [1.0]
    assert len(calls) == 2
    await scraper.aclose()


@pytest.mark.asyncio
async def test_get_tender_details_retries_on_server_error(monkeypatch: pytest.MonkeyPatch):
    cache = MemoryCache()
    patch_cache(monkeypatch, cache)
    delays: list[float] = []
    calls: list[str] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    transport = make_transport(
        responses=[
            httpx.Response(500, text="server error"),
            httpx.Response(500, text="server error"),
            httpx.Response(200, text=DETAIL_HTML),
        ],
        calls=calls,
    )
    scraper = GoszakupScraper(transport=transport, sleep_func=fake_sleep)

    detail = await scraper.get_tender_details(1001)

    assert detail.id == 1001
    assert delays == [1.0, 3.0]
    assert len(calls) == 3
    await scraper.aclose()


@pytest.mark.asyncio
async def test_search_tenders_does_not_retry_on_forbidden(monkeypatch: pytest.MonkeyPatch):
    cache = MemoryCache()
    patch_cache(monkeypatch, cache)
    calls: list[str] = []
    scraper = GoszakupScraper(
        transport=make_transport(responses=[httpx.Response(403, text="forbidden")], calls=calls)
    )

    with pytest.raises(GoszakupForbiddenError):
        await scraper.search_tenders(region="Алматы", limit=1)

    assert len(calls) == 1
    await scraper.aclose()


@pytest.mark.asyncio
async def test_search_tenders_works_when_cache_backend_is_unavailable(monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []

    def broken_get(_key: str) -> object | None:
        raise RuntimeError("redis offline")

    def broken_set(_key: str, _value: object, ttl: int | None = None) -> bool:
        raise RuntimeError("redis offline")

    monkeypatch.setattr("nova.integrations.goszakup.scraper.get_cache", broken_get)
    monkeypatch.setattr("nova.integrations.goszakup.scraper.set_cache", broken_set)
    scraper = GoszakupScraper(transport=make_transport(calls=calls))

    tenders = await scraper.search_tenders(region="Алматы", limit=2)

    assert [tender.id for tender in tenders] == [1001, 1002]
    assert len(calls) == 1
    await scraper.aclose()


@pytest.mark.asyncio
async def test_live_smoke_search_page_opt_in():
    if os.environ.get("RUN_LIVE_GOSZAKUP_TESTS") != "1":
        pytest.skip("Live goszakup smoke test is opt-in")

    scraper = GoszakupScraper()
    try:
        html = await scraper.fetch_search_page(params={"page": "1", "count_record": "1"})
    finally:
        await scraper.aclose()

    assert html
    assert "<html" in html.lower()
