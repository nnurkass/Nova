"""
Tender scoring algorithm for Kazakhstan construction procurement.

Evaluates tenders based on:
- Budget scale & margin suitability (30%)
- Application submission deadline buffer (20%)
- Region compatibility (20%)
- Procurement method / Buy type (15%)
- Customer reliability & history (15%)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from nova.integrations.goszakup.models import Tender, TenderScore


def score_tender(
    tender: Tender,
    target_region_id: Optional[int] = None,
    target_region_name: Optional[str] = None,
) -> TenderScore:
    """Calculate multi-criteria suitability score for a tender."""
    # 1. Budget Score (max 30 pts)
    # Optimal construction contract size for MVP profile: 50M to 500M KZT
    total_sum = float(tender.total_sum or 0.0)
    if total_sum >= 50_000_000 and total_sum <= 500_000_000:
        budget_score = 30.0
    elif total_sum > 500_000_000:
        budget_score = 25.0  # High scale, more risk
    elif total_sum >= 20_000_000:
        budget_score = 20.0
    elif total_sum > 0:
        budget_score = 12.0
    else:
        budget_score = 5.0

    # 2. Deadline Score (max 20 pts)
    deadline_score = 15.0
    if tender.end_date:
        now = datetime.now(timezone.utc) if tender.end_date.tzinfo else datetime.now()
        days_left = (tender.end_date - now).total_seconds() / 86400.0
        if days_left >= 14:
            deadline_score = 20.0
        elif days_left >= 7:
            deadline_score = 16.0
        elif days_left >= 3:
            deadline_score = 10.0
        elif days_left > 0:
            deadline_score = 5.0
        else:
            deadline_score = 0.0

    # 3. Region Score (max 20 pts)
    # Major construction markets in Kazakhstan: Almaty (750000000), Astana (710000000), Shymkent (790000000)
    region_score = 14.0
    if target_region_id and tender.ref_region_id == target_region_id:
        region_score = 20.0
    elif target_region_name:
        t_name = (tender.name_ru + " " + tender.organizer_name_ru + " " + (tender.customer_name_ru or "")).lower()
        clean_target = target_region_name.lower().replace("г.", "").replace("город", "").strip()
        if clean_target and clean_target in t_name:
            region_score = 20.0
        elif (clean_target in {"алматы", "алмат"} and tender.ref_region_id == 750000000) or \
             (clean_target in {"астана", "астан", "нур-султан"} and tender.ref_region_id == 710000000) or \
             (clean_target in {"шымкент", "шымк"} and tender.ref_region_id == 790000000) or \
             (clean_target in {"караганда", "караганд"} and tender.ref_region_id == 350000000):
            region_score = 20.0
        else:
            region_score = 5.0
    elif tender.ref_region_id in {750000000, 710000000, 790000000}:
        region_score = 18.0

    # 4. Purchase Type Score (max 15 pts)
    # 2 = Открытый конкурс (Open tender), 1 = Аукцион, 3 = Запрос ценовых предложений
    if tender.trd_buy_type_id == 2:
        purchase_type_score = 15.0
    elif tender.trd_buy_type_id == 1:
        purchase_type_score = 12.0
    elif tender.trd_buy_type_id == 3:
        purchase_type_score = 10.0
    else:
        purchase_type_score = 8.0

    # 5. History / Customer Reliability Score (max 15 pts)
    customer = (tender.organizer_name_ru + " " + (tender.customer_name_ru or "")).lower()
    if any(k in customer for k in ["управление образования", "акимат", "управление строительства", "коммунального"]):
        history_score = 15.0
    elif any(k in customer for k in ["гу", "кгу", "гп"]):
        history_score = 13.0
    else:
        history_score = 10.0

    total_score = round(
        budget_score + deadline_score + region_score + purchase_type_score + history_score, 1
    )

    if total_score >= 75.0:
        rec = "HIGH"
    elif total_score >= 50.0:
        rec = "MEDIUM"
    else:
        rec = "LOW"

    return TenderScore(
        tender_id=tender.id,
        total_score=total_score,
        budget_score=budget_score,
        deadline_score=deadline_score,
        region_score=region_score,
        purchase_type_score=purchase_type_score,
        history_score=history_score,
        recommendation=rec,
    )


__all__ = ["score_tender"]
