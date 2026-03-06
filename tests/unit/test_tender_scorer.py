"""Unit tests for deterministic tender scoring."""
from __future__ import annotations

from datetime import datetime

from nova.agents.level3.tender_scorer import TenderScoringContext, score_tender
from nova.integrations.goszakup.models import Tender, TenderDocument


def make_tender(**overrides: object) -> Tender:
    payload = {
        "id": 1001,
        "number": "АНО-2026-001",
        "name_ru": "Строительство школы",
        "status_id": 1,
        "trd_buy_type_id": 2,
        "organizer_id": 501,
        "organizer_bin": "123456789012",
        "organizer_name_ru": "Управление строительства Алматы",
        "customer_bin": "987654321098",
        "customer_name_ru": 'ГУ "Отдел образования"',
        "end_date": datetime(2026, 3, 20, 18, 0, 0),
        "total_sum": 250_000_000.0,
        "purchase_type_name_ru": "Открытый конкурс",
        "documents": [
            TenderDocument(
                id=3001,
                name="Техническая спецификация",
                url="https://goszakup.gov.kz/storage/docs/specification.pdf",
            )
        ],
    }
    payload.update(overrides)
    return Tender(**payload)


def test_score_tender_high_priority():
    tender = make_tender()
    context = TenderScoringContext(
        budget_max=260_000_000.0,
        region_matched=True,
        reference_datetime=datetime(2026, 3, 1, 9, 0, 0),
    )

    score = score_tender(tender, context=context)

    assert score.total_score == 100.0
    assert score.budget_score == 30.0
    assert score.deadline_score == 20.0
    assert score.region_score == 20.0
    assert score.purchase_type_score == 15.0
    assert score.history_score == 15.0
    assert score.recommendation == "HIGH"


def test_score_tender_medium_priority():
    tender = make_tender(
        id=1002,
        total_sum=120_000_000.0,
        purchase_type_name_ru="Запрос ценовых предложений",
        documents=[],
        technical_specification=None,
        end_date=datetime(2026, 3, 15, 17, 0, 0),
    )
    context = TenderScoringContext(
        budget_max=100_000_000.0,
        region_matched=None,
        reference_datetime=datetime(2026, 3, 5, 9, 0, 0),
    )

    score = score_tender(tender, context=context)

    assert score.total_score == 57.0
    assert score.budget_score == 12.0
    assert score.deadline_score == 16.0
    assert score.region_score == 10.0
    assert score.purchase_type_score == 9.0
    assert score.history_score == 10.0
    assert score.recommendation == "MEDIUM"


def test_score_tender_low_priority_due_to_budget_and_risk():
    tender = make_tender(
        id=1003,
        total_sum=200_000_000.0,
        purchase_type_name_ru="Из одного источника",
        documents=[],
        technical_specification=None,
        customer_bin=None,
        organizer_bin="bad-bin",
        end_date=datetime(2026, 3, 7, 9, 0, 0),
    )
    context = TenderScoringContext(
        budget_max=100_000_000.0,
        region_matched=False,
        reference_datetime=datetime(2026, 3, 5, 9, 0, 0),
    )

    score = score_tender(tender, context=context)

    assert score.total_score == 6.0
    assert score.budget_score == 0.0
    assert score.deadline_score == 4.0
    assert score.region_score == 0.0
    assert score.purchase_type_score == 2.0
    assert score.history_score == 0.0
    assert score.recommendation == "LOW"


def test_score_tender_penalizes_short_deadline():
    tender = make_tender(end_date=datetime(2026, 3, 5, 21, 0, 0))
    context = TenderScoringContext(
        budget_max=300_000_000.0,
        region_matched=True,
        reference_datetime=datetime(2026, 3, 5, 9, 0, 0),
    )

    score = score_tender(tender, context=context)

    assert score.deadline_score == 0.0
    assert score.total_score == 80.0
    assert score.recommendation == "HIGH"


def test_score_tender_uses_neutral_defaults_without_context():
    tender = make_tender(
        id=1004,
        end_date=None,
        total_sum=None,
        purchase_type_name_ru=None,
        customer_bin=None,
        organizer_bin="",
        documents=[],
        technical_specification=None,
    )

    score = score_tender(tender)

    assert score.budget_score == 15.0
    assert score.deadline_score == 0.0
    assert score.region_score == 10.0
    assert score.purchase_type_score == 5.0
    assert score.history_score == 0.0
    assert score.total_score == 30.0
    assert score.recommendation == "LOW"
