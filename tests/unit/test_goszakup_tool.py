"""Unit tests for goszakup LangChain tools."""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from nova.agents.level3.goszakup_tool import goszakup_search
from nova.integrations.goszakup.scraper import DETAIL_PATH_TEMPLATE, SEARCH_PATH, GoszakupScraper


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


def patch_cache(monkeypatch: pytest.MonkeyPatch, cache: MemoryCache) -> None:
    monkeypatch.setattr("nova.integrations.goszakup.scraper.get_cache", cache.get)
    monkeypatch.setattr("nova.integrations.goszakup.scraper.set_cache", cache.set)


def make_transport(
    *,
    search_html: str = SEARCH_HTML,
    detail_html: str = DETAIL_HTML,
) -> httpx.MockTransport:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SEARCH_PATH:
            return httpx.Response(200, text=search_html)
        if request.url.path == DETAIL_PATH_TEMPLATE.format(tender_id=1001):
            return httpx.Response(200, text=detail_html)
        return httpx.Response(404, text="not found")

    return httpx.MockTransport(handler)


def scraper_factory(*, search_html: str = SEARCH_HTML, detail_html: str = DETAIL_HTML):
    def factory() -> GoszakupScraper:
        return GoszakupScraper(transport=make_transport(search_html=search_html, detail_html=detail_html))

    return factory


def test_goszakup_search_returns_scored_json(monkeypatch: pytest.MonkeyPatch):
    patch_cache(monkeypatch, MemoryCache())
    monkeypatch.setattr(
        "nova.agents.level3.goszakup_tool._create_scraper",
        scraper_factory(),
    )

    result = goszakup_search.invoke(
        {
            "region": "Алматы",
            "budget_max": 300_000_000,
            "limit": 2,
            "reference_datetime": "2026-03-01T09:00:00",
        }
    )
    payload = json.loads(result)

    assert payload["tool"] == "goszakup_search"
    assert payload["status"] == "ok"
    assert payload["summary"]["returned"] == 2
    assert payload["summary"]["high_priority"] == 2
    assert payload["tenders"][0]["id"] == 1001
    assert payload["tenders"][0]["score_preview"]["recommendation"] == "HIGH"
    assert payload["tenders"][0]["score_preview"]["total_score"] > payload["tenders"][1]["score_preview"]["total_score"]
