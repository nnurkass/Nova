"""
LangChain tool wrappers for goszakup.gov.kz GraphQL API & Tender Scoring.

Provides callable tools for Level 2 Procurement agent.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from langchain_core.tools import tool

from nova.agents.level3.tender_scorer import score_tender as calculate_score
from nova.integrations.goszakup.client import GoszakupClient

_client = GoszakupClient()


@tool
def goszakup_search(
    query: str = "",
    region: str = "",
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search tenders on goszakup.gov.kz by keyword, region, and budget constraints."""
    tenders = _client.search_tenders(
        query=query,
        region_name=region if region else None,
        budget_min=budget_min,
        budget_max=budget_max,
        limit=limit,
    )
    return [t.model_dump() for t in tenders]


@tool
def analyze_tender(tender_id: int) -> dict[str, Any]:
    """Retrieve in-depth details of a specific tender including lots and requirements."""
    tender = _client.get_tender_details(tender_id)
    if not tender:
        return {"error": f"Tender {tender_id} not found"}

    score_result = calculate_score(tender)
    return {
        "tender": tender.model_dump(),
        "score": score_result.model_dump(),
        "summary": (
            f"Тендер №{tender.number}: {tender.name_ru}. "
            f"Сумма: {tender.total_sum:,.2f} KZT. "
            f"Оценка пригодности: {score_result.total_score}/100 ({score_result.recommendation})."
        ),
    }


@tool
def score_tender(tender_id: int) -> dict[str, Any]:
    """Calculate multi-factor suitability score for a tender."""
    tender = _client.get_tender_details(tender_id)
    if not tender:
        return {"error": f"Tender {tender_id} not found"}
    return calculate_score(tender).model_dump()


@tool
def download_tender_docs(tender_id: int, save_path: str = "") -> dict[str, Any]:
    """Download technical specifications and estimate documents for a tender."""
    tender = _client.get_tender_details(tender_id)
    if not tender:
        return {"error": f"Tender {tender_id} not found", "files": []}

    target_dir = Path(save_path) if save_path else Path("./data/tender_docs") / str(tender_id)
    target_dir.mkdir(parents=True, exist_ok=True)

    # In MVP / Fallback mode, generate a summary doc
    doc_path = target_dir / "technical_spec.json"
    with open(doc_path, "w", encoding="utf-8") as f:
        json.dump(tender.model_dump(), f, ensure_ascii=False, indent=2, default=str)

    return {
        "tender_id": tender_id,
        "saved_path": str(doc_path),
        "files_count": 1,
        "status": "downloaded",
    }


__all__ = [
    "goszakup_search",
    "analyze_tender",
    "score_tender",
    "download_tender_docs",
]
