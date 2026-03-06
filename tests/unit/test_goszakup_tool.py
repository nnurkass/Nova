"""Unit tests for goszakup LangChain tools."""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from nova.agents.level3.goszakup_tool import analyze_tender, download_tender_docs, goszakup_search
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
    document_payloads: dict[str, bytes] | None = None,
    failing_paths: set[str] | None = None,
) -> httpx.MockTransport:
    payloads = document_payloads or {
        "/storage/docs/specification.pdf": b"%PDF-1.4 fake pdf bytes",
        "/storage/docs/estimate.xlsx": b"PK\x03\x04fake xlsx bytes",
    }
    failures = failing_paths or set()

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SEARCH_PATH:
            return httpx.Response(200, text=search_html)
        if request.url.path == DETAIL_PATH_TEMPLATE.format(tender_id=1001):
            return httpx.Response(200, text=detail_html)
        if request.url.path in failures:
            return httpx.Response(500, text="download failed")
        if request.url.path in payloads:
            return httpx.Response(200, content=payloads[request.url.path])
        return httpx.Response(404, text="not found")

    return httpx.MockTransport(handler)


def scraper_factory(
    *,
    search_html: str = SEARCH_HTML,
    detail_html: str = DETAIL_HTML,
    document_payloads: dict[str, bytes] | None = None,
    failing_paths: set[str] | None = None,
):
    def factory() -> GoszakupScraper:
        return GoszakupScraper(
            transport=make_transport(
                search_html=search_html,
                detail_html=detail_html,
                document_payloads=document_payloads,
                failing_paths=failing_paths,
            )
        )

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


def test_analyze_tender_returns_score_breakdown_and_risk_flags(monkeypatch: pytest.MonkeyPatch):
    degraded_detail_html = (
        DETAIL_HTML
        .replace(
            '<div data-field="purchase_type_name_ru">Открытый конкурс</div>',
            '<div data-field="purchase_type_name_ru">Из одного источника</div>',
        )
        .replace(
            '<div data-field="end_date">2026-03-20T18:00:00</div>',
            '<div data-field="end_date">2026-03-19T12:00:00</div>',
        )
        .replace(
            '<div data-field="total_sum">250000000.00</div>',
            '<div data-field="total_sum"></div>',
        )
        .replace(
            """<section class="technical-specification">
        <div data-field="technical_specification">
          Выполнить строительно-монтажные работы, благоустройство территории
          и поставку оборудования для школы.
        </div>
      </section>
""",
            """<section class="technical-specification">
        <div data-field="technical_specification"></div>
      </section>
""",
        )
        .replace(
            """<section class="lots">
        <div class="tender-lot" data-role="tender-lot" data-lot-id="9001" data-lot-number="1">
          <div class="lot-name" data-field="name_ru">Строительно-монтажные работы</div>
          <div data-field="name_kz">Құрылыс-монтаж жұмыстары</div>
          <div data-field="amount">1</div>
          <div data-field="count">1</div>
          <div data-field="unit">услуга</div>
        </div>
        <div class="tender-lot" data-role="tender-lot" data-lot-id="9002" data-lot-number="2">
          <div class="lot-name" data-field="name_ru">Поставка оборудования</div>
          <div data-field="amount">1200</div>
          <div data-field="count">1200</div>
          <div data-field="unit">комплект</div>
        </div>
      </section>
""",
            """<section class="lots">
      </section>
""",
        )
        .replace(
            """<section class="documents">
        <ul>
          <li class="document-item" data-role="document-item" data-document-id="3001">
            <a href="/storage/docs/specification.pdf">Техническая спецификация</a>
            <div data-field="category">specification</div>
            <div data-field="published_at">2026-03-01T10:05:00</div>
          </li>
          <li class="document-item" data-role="document-item" data-document-id="3002">
            <a href="/storage/docs/estimate.xlsx">Смета</a>
            <div data-field="category">estimate</div>
            <div data-field="published_at">2026-03-01T10:06:00</div>
          </li>
        </ul>
      </section>
""",
            """<section class="documents">
        <ul></ul>
      </section>
""",
        )
    )
    patch_cache(monkeypatch, MemoryCache())
    monkeypatch.setattr(
        "nova.agents.level3.goszakup_tool._create_scraper",
        scraper_factory(detail_html=degraded_detail_html),
    )

    result = analyze_tender.invoke(
        {
            "tender_id": 1001,
            "budget_max": 150_000_000,
            "scoring_region_matched": False,
            "reference_datetime": "2026-03-19T09:00:00",
        }
    )
    payload = json.loads(result)

    assert payload["tool"] == "analyze_tender"
    assert payload["status"] == "ok"
    assert payload["recommendation"] == "LOW"
    assert payload["score_breakdown"]["purchase_type_score"] == 2.0
    assert payload["document_count"] == 0
    assert payload["lot_count"] == 0
    assert payload["risk_flags"] == [
        "missing_technical_specification",
        "missing_documents",
        "short_submission_window",
        "budget_unknown",
        "missing_lots",
        "weak_purchase_type",
    ]


def test_download_tender_docs_saves_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    patch_cache(monkeypatch, MemoryCache())
    monkeypatch.setattr(
        "nova.agents.level3.goszakup_tool._create_scraper",
        scraper_factory(),
    )

    result = download_tender_docs.invoke(
        {
            "tender_id": 1001,
            "save_path": str(tmp_path),
        }
    )
    payload = json.loads(result)

    assert payload["tool"] == "download_tender_docs"
    assert payload["status"] == "ok"
    assert payload["downloaded_count"] == 2
    assert payload["errors"] == []
    saved_paths = [Path(item["path"]) for item in payload["files"]]
    assert {path.suffix for path in saved_paths} == {".pdf", ".xlsx"}
    assert all(path.exists() for path in saved_paths)


def test_download_tender_docs_handles_empty_document_list(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    empty_docs_html = DETAIL_HTML.replace(
        """<section class="documents">
        <ul>
          <li class="document-item" data-role="document-item" data-document-id="3001">
            <a href="/storage/docs/specification.pdf">Техническая спецификация</a>
            <div data-field="category">specification</div>
            <div data-field="published_at">2026-03-01T10:05:00</div>
          </li>
          <li class="document-item" data-role="document-item" data-document-id="3002">
            <a href="/storage/docs/estimate.xlsx">Смета</a>
            <div data-field="category">estimate</div>
            <div data-field="published_at">2026-03-01T10:06:00</div>
          </li>
        </ul>
      </section>
""",
        """<section class="documents">
        <ul></ul>
      </section>
""",
    )
    patch_cache(monkeypatch, MemoryCache())
    monkeypatch.setattr(
        "nova.agents.level3.goszakup_tool._create_scraper",
        scraper_factory(detail_html=empty_docs_html),
    )

    result = download_tender_docs.invoke(
        {
            "tender_id": 1001,
            "save_path": str(tmp_path),
        }
    )
    payload = json.loads(result)

    assert payload["document_count"] == 0
    assert payload["downloaded_count"] == 0
    assert payload["files"] == []
    assert payload["errors"] == []


def test_download_tender_docs_records_partial_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    patch_cache(monkeypatch, MemoryCache())
    monkeypatch.setattr(
        "nova.agents.level3.goszakup_tool._create_scraper",
        scraper_factory(failing_paths={"/storage/docs/estimate.xlsx"}),
    )

    result = download_tender_docs.invoke(
        {
            "tender_id": 1001,
            "save_path": str(tmp_path),
        }
    )
    payload = json.loads(result)

    assert payload["downloaded_count"] == 1
    assert len(payload["files"]) == 1
    assert len(payload["errors"]) == 1
    assert payload["errors"][0]["name"] == "Смета"
