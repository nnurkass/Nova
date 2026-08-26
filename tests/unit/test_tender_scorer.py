"""Unit tests for tender scoring algorithm."""
from datetime import datetime, timedelta, timezone

from nova.agents.level3.tender_scorer import score_tender
from nova.integrations.goszakup.models import Tender, TenderLot


def _create_test_tender(
    tender_id: int = 1,
    name: str = "Капитальный ремонт",
    total_sum: float = 100_000_000.0,
    ref_region_id: int = 750000000,
    trd_buy_type_id: int = 2,
    days_to_end: int = 15,
) -> Tender:
    end_date = datetime.now(timezone.utc) + timedelta(days=days_to_end)
    return Tender(
        id=tender_id,
        number=f"TND-{tender_id}",
        name_ru=name,
        status_id=1,
        trd_buy_type_id=trd_buy_type_id,
        organizer_id=1,
        organizer_bin="990140001234",
        organizer_name_ru="ГУ «Управление строительства г. Алматы»",
        total_sum=total_sum,
        end_date=end_date,
        ref_region_id=ref_region_id,
        lots=[TenderLot(id=1, lot_number=1, name_ru="СМР", amount=total_sum, count=1.0, unit="усл")],
    )


class TestTenderScorer:
    def test_high_priority_tender_scoring(self):
        tender = _create_test_tender(
            total_sum=150_000_000.0,
            days_to_end=20,
            ref_region_id=750000000,
        )
        score = score_tender(tender, target_region_id=750000000)
        assert score.total_score >= 75.0
        assert score.recommendation == "HIGH"
        assert score.budget_score == 30.0
        assert score.deadline_score == 20.0
        assert score.region_score == 20.0

    def test_low_priority_tender_scoring(self):
        tender = _create_test_tender(
            total_sum=5_000_000.0,
            days_to_end=1,
            ref_region_id=100000000,
            trd_buy_type_id=4,
        )
        score = score_tender(tender, target_region_id=750000000)
        assert score.total_score < 60.0
        assert score.budget_score < 20.0
        assert score.deadline_score <= 5.0
