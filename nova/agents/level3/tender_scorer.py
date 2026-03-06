"""Deterministic tender scoring helpers for procurement tools."""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from nova.integrations.goszakup.models import Tender, TenderScore


class TenderScoringContext(BaseModel):
    """Optional operator preferences used to score a tender."""

    budget_max: float | None = Field(default=None, ge=0)
    region_matched: bool | None = None
    reference_datetime: datetime | None = None


PURCHASE_TYPE_SCORES: tuple[tuple[str, float], ...] = (
    ("открытый конкурс", 15.0),
    ("конкурс с использованием рейтингово-балльной системы", 14.0),
    ("конкурс", 12.0),
    ("аукцион", 13.0),
    ("запрос ценовых предложений", 9.0),
    ("запрос предложений", 8.0),
    ("товарная биржа", 6.0),
    ("из одного источника", 2.0),
)


def score_tender(tender: Tender, context: TenderScoringContext | None = None) -> TenderScore:
    """Return a deterministic tender score based on configured heuristics."""
    context = context or TenderScoringContext()
    budget_score = _score_budget(tender.total_sum, context.budget_max)
    deadline_score = _score_deadline(tender.end_date, context.reference_datetime)
    region_score = _score_region(context.region_matched)
    purchase_type_score = _score_purchase_type(tender.purchase_type_name_ru)
    history_score = _score_history(tender)

    total_score = round(
        budget_score + deadline_score + region_score + purchase_type_score + history_score,
        2,
    )

    return TenderScore(
        tender_id=tender.id,
        total_score=total_score,
        budget_score=budget_score,
        deadline_score=deadline_score,
        region_score=region_score,
        purchase_type_score=purchase_type_score,
        history_score=history_score,
        recommendation=_recommendation_for_score(total_score),
    )


def _score_budget(total_sum: float | None, budget_max: float | None) -> float:
    if budget_max is None:
        return 15.0
    if total_sum is None:
        return 0.0
    if total_sum <= budget_max:
        return 30.0
    if total_sum <= budget_max * 1.15:
        return 21.0
    if total_sum <= budget_max * 1.30:
        return 12.0
    return 0.0


def _score_deadline(end_date: datetime | None, reference_datetime: datetime | None) -> float:
    if end_date is None:
        return 0.0

    deadline = _normalize_datetime(end_date)
    reference = _normalize_datetime(reference_datetime or datetime.now(timezone.utc))
    days_remaining = (deadline - reference).total_seconds() / 86_400

    if days_remaining > 14:
        return 20.0
    if days_remaining >= 8:
        return 16.0
    if days_remaining >= 4:
        return 10.0
    if days_remaining >= 1:
        return 4.0
    return 0.0


def _score_region(region_matched: bool | None) -> float:
    if region_matched is True:
        return 20.0
    if region_matched is False:
        return 0.0
    return 10.0


def _score_purchase_type(purchase_type_name: str | None) -> float:
    if not purchase_type_name:
        return 5.0

    normalized = " ".join(purchase_type_name.casefold().split())
    for label, score in PURCHASE_TYPE_SCORES:
        if label in normalized:
            return score
    return 7.0


def _score_history(tender: Tender) -> float:
    score = 0.0
    if tender.customer_bin:
        score += 5.0
    if _is_valid_bin(tender.organizer_bin):
        score += 5.0
    if tender.documents or tender.technical_specification:
        score += 5.0
    return score


def _is_valid_bin(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip()
    return len(normalized) == 12 and normalized.isdigit()


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _recommendation_for_score(total_score: float) -> str:
    if total_score >= 75:
        return "HIGH"
    if total_score >= 45:
        return "MEDIUM"
    return "LOW"


__all__ = ["TenderScoringContext", "score_tender"]
