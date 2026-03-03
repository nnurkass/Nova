"""Unit tests for Step 1.3 — SharedState and data models."""
import pytest
from datetime import datetime, timezone


# ── 1.3.2  Goszakup models ────────────────────────────────────────────
class TestGoszakupModels:
    def test_tender_lot_creation(self):
        from nova.integrations.goszakup.models import TenderLot
        lot = TenderLot(id=1, lot_number=1, name_ru="Лот 1")
        assert lot.id == 1
        assert lot.amount is None

    def test_tender_creation(self):
        from nova.integrations.goszakup.models import Tender
        tender = Tender(
            id=100,
            number="АНО-2026-001",
            name_ru="Строительство дороги",
            status_id=1,
            trd_buy_type_id=2,
            organizer_id=10,
            organizer_bin="123456789012",
            organizer_name_ru="АО Тест",
        )
        assert tender.id == 100
        assert tender.lots == []
        assert tender.total_sum is None

    def test_tender_search_filter_defaults(self):
        from nova.integrations.goszakup.models import TenderSearchFilter
        f = TenderSearchFilter()
        assert f.limit == 10
        assert f.region_id is None

    def test_tender_score_recommendation(self):
        from nova.integrations.goszakup.models import TenderScore
        score = TenderScore(
            tender_id=100,
            total_score=85.0,
            budget_score=28.0,
            deadline_score=18.0,
            region_score=18.0,
            purchase_type_score=12.0,
            history_score=9.0,
            recommendation="HIGH",
        )
        assert score.total_score == 85.0
        assert score.recommendation == "HIGH"
