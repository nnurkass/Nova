"""LangChain tools for goszakup.gov.kz search workflows."""
from __future__ import annotations

import asyncio
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from nova.agents.level3.tender_scorer import TenderScoringContext, score_tender
from nova.integrations.goszakup import GoszakupScraper, Tender, TenderScore


class TenderSearchToolInput(BaseModel):
    """Input schema for `goszakup_search`."""

    region: str | None = Field(default=None, description="Tender region filter.")
    work_type: str | None = Field(default=None, description="Search phrase or work type.")
    budget_min: float | None = Field(default=None, ge=0, description="Minimum tender budget.")
    budget_max: float | None = Field(default=None, ge=0, description="Maximum tender budget.")
    deadline_from: datetime | None = Field(
        default=None,
        description="Lower bound for submission deadline in ISO-8601 format.",
    )
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of tenders to return.")
    scoring_region_matched: bool | None = Field(
        default=None,
        description="Override for region matching in score preview.",
    )
    reference_datetime: datetime | None = Field(
        default=None,
        description="Reference timestamp for deadline scoring.",
    )


class TenderAnalysisToolInput(BaseModel):
    """Input schema for `analyze_tender`."""

    tender_id: int = Field(..., gt=0, description="Tender identifier from goszakup.gov.kz.")
    budget_max: float | None = Field(default=None, ge=0, description="Preferred maximum budget.")
    scoring_region_matched: bool | None = Field(
        default=None,
        description="Override for region matching in tender analysis.",
    )
    reference_datetime: datetime | None = Field(
        default=None,
        description="Reference timestamp for deadline scoring.",
    )


class TenderDownloadToolInput(BaseModel):
    """Input schema for `download_tender_docs`."""

    tender_id: int = Field(..., gt=0, description="Tender identifier from goszakup.gov.kz.")
    save_path: str = Field(..., min_length=1, description="Directory where tender documents will be saved.")


def _create_scraper() -> GoszakupScraper:
    return GoszakupScraper()


def _run_async(awaitable: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, awaitable)
        return future.result()


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _tool_error(tool_name: str, exc: Exception) -> str:
    return _json_dumps(
        {
            "tool": tool_name,
            "status": "error",
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }
    )


def _build_scoring_context(
    *,
    budget_max: float | None,
    region: str | None = None,
    scoring_region_matched: bool | None = None,
    reference_datetime: datetime | None = None,
) -> TenderScoringContext:
    region_matched = scoring_region_matched
    if region_matched is None and region is not None:
        region_matched = True

    return TenderScoringContext(
        budget_max=budget_max,
        region_matched=region_matched,
        reference_datetime=reference_datetime,
    )


def _serialize_score(score: TenderScore) -> dict[str, Any]:
    return score.model_dump(mode="json")


def _serialize_tender(
    tender: Tender,
    *,
    score: TenderScore | None = None,
    include_documents: bool = False,
    include_lots: bool = False,
) -> dict[str, Any]:
    payload = {
        "id": tender.id,
        "number": tender.number,
        "name_ru": tender.name_ru,
        "status_name_ru": tender.status_name_ru,
        "purchase_type_name_ru": tender.purchase_type_name_ru,
        "organizer_name_ru": tender.organizer_name_ru,
        "customer_name_ru": tender.customer_name_ru,
        "total_sum": tender.total_sum,
        "end_date": tender.end_date.isoformat() if tender.end_date else None,
        "detail_url": tender.detail_url,
    }
    if include_documents:
        payload["documents"] = [
            {
                "id": document.id,
                "name": document.name,
                "url": document.url,
                "category": document.category,
                "published_at": document.published_at.isoformat() if document.published_at else None,
            }
            for document in tender.documents
        ]
    if include_lots:
        payload["lots"] = [
            {
                "id": lot.id,
                "lot_number": lot.lot_number,
                "name_ru": lot.name_ru,
                "amount": lot.amount,
                "count": lot.count,
                "unit": lot.unit,
            }
            for lot in tender.lots
        ]
    if score is not None:
        payload["score_preview"] = _serialize_score(score)
    return payload


def _summarize_scores(scored_tenders: list[tuple[Tender, TenderScore]]) -> dict[str, Any]:
    return {
        "returned": len(scored_tenders),
        "high_priority": sum(score.recommendation == "HIGH" for _, score in scored_tenders),
        "medium_priority": sum(score.recommendation == "MEDIUM" for _, score in scored_tenders),
        "low_priority": sum(score.recommendation == "LOW" for _, score in scored_tenders),
        "top_score": max((score.total_score for _, score in scored_tenders), default=0.0),
    }


def _excerpt_text(text: str | None, *, limit: int = 280) -> str:
    if not text:
        return ""
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3].rstrip()}..."


def _days_until_deadline(end_date: datetime | None, reference_datetime: datetime | None) -> float | None:
    if end_date is None:
        return None

    reference = reference_datetime or datetime.now()
    deadline = end_date
    if deadline.tzinfo is not None:
        deadline = deadline.astimezone().replace(tzinfo=None)
    if reference.tzinfo is not None:
        reference = reference.astimezone().replace(tzinfo=None)
    return (deadline - reference).total_seconds() / 86_400


def _build_risk_flags(
    tender: Tender,
    *,
    score: TenderScore,
    reference_datetime: datetime | None,
) -> list[str]:
    risk_flags: list[str] = []
    if not tender.technical_specification:
        risk_flags.append("missing_technical_specification")
    if not tender.documents:
        risk_flags.append("missing_documents")
    days_until_deadline = _days_until_deadline(tender.end_date, reference_datetime)
    if days_until_deadline is not None and days_until_deadline < 4:
        risk_flags.append("short_submission_window")
    if tender.total_sum is None:
        risk_flags.append("budget_unknown")
    if not tender.lots:
        risk_flags.append("missing_lots")
    if score.purchase_type_score <= 5:
        risk_flags.append("weak_purchase_type")
    return risk_flags


def _sanitize_filename(value: str) -> str:
    normalized = " ".join(value.split()).strip()
    sanitized = re.sub(r"[^\w.-]+", "_", normalized, flags=re.UNICODE).strip("._")
    return sanitized or "document"


def _build_document_filename(document_name: str, document_url: str, *, index: int) -> str:
    parsed_url = urlparse(document_url)
    url_name = Path(unquote(parsed_url.path)).name
    source_name = document_name.strip() or url_name or f"document_{index}"

    source_path = Path(source_name)
    suffix = source_path.suffix or Path(url_name).suffix
    stem = source_path.stem if source_path.suffix else source_name
    safe_stem = _sanitize_filename(stem)
    safe_suffix = _sanitize_filename(suffix) if suffix else ""

    if safe_suffix and not safe_suffix.startswith("."):
        safe_suffix = f".{safe_suffix}"
    return f"{safe_stem}{safe_suffix}"


def _unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    for index in range(2, 1_000):
        next_candidate = directory / f"{stem}_{index}{suffix}"
        if not next_candidate.exists():
            return next_candidate
    raise RuntimeError(f"Unable to allocate unique filename for {filename!r}")


async def _goszakup_search_async(
    *,
    region: str | None = None,
    work_type: str | None = None,
    budget_min: float | None = None,
    budget_max: float | None = None,
    deadline_from: datetime | None = None,
    limit: int = 10,
    scoring_region_matched: bool | None = None,
    reference_datetime: datetime | None = None,
) -> str:
    try:
        async with _create_scraper() as scraper:
            tenders = await scraper.search_tenders(
                region=region,
                work_type=work_type,
                budget_min=budget_min,
                budget_max=budget_max,
                deadline_from=deadline_from,
                limit=limit,
            )
    except Exception as exc:  # pragma: no cover - covered by tool error contract tests later
        return _tool_error("goszakup_search", exc)

    context = _build_scoring_context(
        budget_max=budget_max,
        region=region,
        scoring_region_matched=scoring_region_matched,
        reference_datetime=reference_datetime,
    )
    scored_tenders = [(tender, score_tender(tender, context=context)) for tender in tenders]
    scored_tenders.sort(key=lambda item: item[1].total_score, reverse=True)

    return _json_dumps(
        {
            "tool": "goszakup_search",
            "status": "ok",
            "search_filters": {
                "region": region,
                "work_type": work_type,
                "budget_min": budget_min,
                "budget_max": budget_max,
                "deadline_from": deadline_from.isoformat() if deadline_from else None,
                "limit": limit,
            },
            "summary": _summarize_scores(scored_tenders),
            "tenders": [
                _serialize_tender(tender, score=score)
                for tender, score in scored_tenders
            ],
        }
    )


def _goszakup_search_sync(**kwargs: Any) -> str:
    return _run_async(_goszakup_search_async(**kwargs))


async def _analyze_tender_async(
    *,
    tender_id: int,
    budget_max: float | None = None,
    scoring_region_matched: bool | None = None,
    reference_datetime: datetime | None = None,
) -> str:
    try:
        async with _create_scraper() as scraper:
            tender = await scraper.get_tender_details(tender_id)
    except Exception as exc:  # pragma: no cover - covered by tool error contract tests later
        return _tool_error("analyze_tender", exc)

    context = _build_scoring_context(
        budget_max=budget_max,
        scoring_region_matched=scoring_region_matched,
        reference_datetime=reference_datetime,
    )
    score = score_tender(tender, context=context)
    risk_flags = _build_risk_flags(
        tender,
        score=score,
        reference_datetime=reference_datetime,
    )

    return _json_dumps(
        {
            "tool": "analyze_tender",
            "status": "ok",
            "tender": _serialize_tender(
                tender,
                score=score,
                include_documents=True,
                include_lots=True,
            ),
            "score_breakdown": _serialize_score(score),
            "risk_flags": risk_flags,
            "lot_count": len(tender.lots),
            "document_count": len(tender.documents),
            "technical_specification_excerpt": _excerpt_text(tender.technical_specification),
            "recommendation": score.recommendation,
        }
    )


def _analyze_tender_sync(**kwargs: Any) -> str:
    return _run_async(_analyze_tender_async(**kwargs))


async def _download_tender_docs_async(*, tender_id: int, save_path: str) -> str:
    root_dir = Path(save_path).expanduser().resolve()
    tender_dir = root_dir / f"tender_{tender_id}"
    tender_dir.mkdir(parents=True, exist_ok=True)

    try:
        async with _create_scraper() as scraper:
            tender = await scraper.get_tender_details(tender_id)
            downloaded_files: list[dict[str, Any]] = []
            errors: list[dict[str, Any]] = []

            for index, document in enumerate(tender.documents, start=1):
                try:
                    content = await scraper.download_document(document.url)
                    filename = _build_document_filename(document.name, document.url, index=index)
                    target_path = _unique_path(tender_dir, filename)
                    target_path.write_bytes(content)
                    downloaded_files.append(
                        {
                            "document_id": document.id,
                            "name": document.name,
                            "category": document.category,
                            "path": str(target_path),
                            "size_bytes": len(content),
                            "url": document.url,
                        }
                    )
                except Exception as exc:
                    errors.append(
                        {
                            "document_id": document.id,
                            "name": document.name,
                            "url": document.url,
                            "error_type": exc.__class__.__name__,
                            "error": str(exc),
                        }
                    )
    except Exception as exc:  # pragma: no cover - covered by tool error contract tests later
        return _tool_error("download_tender_docs", exc)

    return _json_dumps(
        {
            "tool": "download_tender_docs",
            "status": "ok",
            "tender_id": tender_id,
            "download_dir": str(tender_dir),
            "document_count": len(tender.documents),
            "downloaded_count": len(downloaded_files),
            "files": downloaded_files,
            "errors": errors,
        }
    )


def _download_tender_docs_sync(**kwargs: Any) -> str:
    return _run_async(_download_tender_docs_async(**kwargs))


goszakup_search = StructuredTool.from_function(
    func=_goszakup_search_sync,
    coroutine=_goszakup_search_async,
    name="goszakup_search",
    description=(
        "Search goszakup.gov.kz tenders and return a JSON payload with tender fields, "
        "summary counts, and deterministic score previews."
    ),
    args_schema=TenderSearchToolInput,
)


analyze_tender = StructuredTool.from_function(
    func=_analyze_tender_sync,
    coroutine=_analyze_tender_async,
    name="analyze_tender",
    description=(
        "Load a single tender card from goszakup.gov.kz and return a JSON analysis with "
        "score breakdown, rule-based risk flags, document counts, and recommendation."
    ),
    args_schema=TenderAnalysisToolInput,
)


download_tender_docs = StructuredTool.from_function(
    func=_download_tender_docs_sync,
    coroutine=_download_tender_docs_async,
    name="download_tender_docs",
    description=(
        "Download tender attachments from goszakup.gov.kz into a local directory and return "
        "a JSON payload with saved file paths plus partial download errors."
    ),
    args_schema=TenderDownloadToolInput,
)


__all__ = [
    "TenderAnalysisToolInput",
    "TenderDownloadToolInput",
    "TenderSearchToolInput",
    "analyze_tender",
    "download_tender_docs",
    "goszakup_search",
]
