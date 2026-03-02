"""Unit tests for SharedState and all Pydantic data models (Step 1.3)."""

from datetime import datetime, timezone

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from nova.api.schemas import (
    AgentReport,
    TaskRequest,
    TaskResponse,
    TaskStatus,
    TaskStatusEnum,
)
from nova.graph.state import ConstructionState
from nova.integrations.abc.models import (
    ABCMaterial,
    ABCWork,
    EstimatePosition,
    ResourceStatement,
)
from nova.integrations.goszakup.models import (
    Tender,
    TenderLot,
    TenderScore,
    TenderSearchFilter,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc)


def make_tender_lot(**kwargs) -> TenderLot:
    defaults = dict(id="lot-1", lot_number=1, name="Lot One", budget=500_000.0, quantity=10.0, unit="шт")
    return TenderLot(**{**defaults, **kwargs})


def make_tender(**kwargs) -> Tender:
    defaults = dict(id="t-1", number="2026-001", name="Road repair", budget=1_000_000.0, status="ACTIVE")
    return Tender(**{**defaults, **kwargs})


def make_abc_work(**kwargs) -> ABCWork:
    defaults = dict(code="W-001", name="Earthwork", unit="м3", quantity=100.0)
    return ABCWork(**{**defaults, **kwargs})


def make_abc_material(**kwargs) -> ABCMaterial:
    defaults = dict(code="M-001", name="Cement M400", unit="кг", quantity=500.0)
    return ABCMaterial(**{**defaults, **kwargs})


# ---------------------------------------------------------------------------
# TenderLot tests
# ---------------------------------------------------------------------------


class TestTenderLot:
    def test_required_fields(self):
        lot = make_tender_lot()
        assert lot.id == "lot-1"
        assert lot.lot_number == 1
        assert lot.name == "Lot One"
        assert lot.budget == 500_000.0
        assert lot.quantity == 10.0
        assert lot.unit == "шт"

    def test_optional_fields_default_none(self):
        lot = make_tender_lot()
        assert lot.delivery_date is None
        assert lot.description is None

    def test_optional_fields_populated(self):
        lot = make_tender_lot(delivery_date=NOW, description="desc")
        assert lot.delivery_date == NOW
        assert lot.description == "desc"

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            TenderLot(id="x", lot_number=1, name="X", budget=100.0, quantity=1.0)  # unit missing


# ---------------------------------------------------------------------------
# Tender tests
# ---------------------------------------------------------------------------


class TestTender:
    def test_minimal_creation(self):
        t = make_tender()
        assert t.id == "t-1"
        assert t.status == "ACTIVE"
        assert t.lots == []
        assert t.documents == []

    def test_optional_fields_default_none(self):
        t = make_tender()
        assert t.publish_date is None
        assert t.region is None
        assert t.organizer_name is None
        assert t.organizer_bin is None
        assert t.tender_subject is None

    def test_with_lots(self):
        lot = make_tender_lot()
        t = make_tender(lots=[lot])
        assert len(t.lots) == 1
        assert t.lots[0].id == "lot-1"

    def test_with_documents(self):
        t = make_tender(documents=["https://example.com/doc.pdf"])
        assert len(t.documents) == 1

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            Tender(id="x", number="001", name="X", status="ACTIVE")  # budget missing


# ---------------------------------------------------------------------------
# TenderSearchFilter tests
# ---------------------------------------------------------------------------


class TestTenderSearchFilter:
    def test_defaults(self):
        f = TenderSearchFilter()
        assert f.status == "ACTIVE"
        assert f.limit == 20
        assert f.region is None
        assert f.budget_min is None
        assert f.budget_max is None

    def test_custom_values(self):
        f = TenderSearchFilter(region="Алматы", work_type="road", budget_min=100_000.0, budget_max=5_000_000.0, limit=10)
        assert f.region == "Алматы"
        assert f.work_type == "road"
        assert f.limit == 10

    def test_deadline_filters(self):
        f = TenderSearchFilter(deadline_from=NOW, deadline_to=NOW)
        assert f.deadline_from == NOW
        assert f.deadline_to == NOW


# ---------------------------------------------------------------------------
# TenderScore tests
# ---------------------------------------------------------------------------


class TestTenderScore:
    def test_creation(self):
        score = TenderScore(
            tender_id="t-1",
            budget_score=80.0,
            deadline_score=70.0,
            region_score=90.0,
            purchase_type_score=75.0,
            organizer_history_score=65.0,
            total_score=76.0,
            recommendation="HIGH",
        )
        assert score.total_score == 76.0
        assert score.recommendation == "HIGH"

    def test_recommendation_values(self):
        for rec in ("HIGH", "MEDIUM", "LOW"):
            score = TenderScore(
                tender_id="t-1",
                budget_score=50.0,
                deadline_score=50.0,
                region_score=50.0,
                purchase_type_score=50.0,
                organizer_history_score=50.0,
                total_score=50.0,
                recommendation=rec,
            )
            assert score.recommendation == rec


# ---------------------------------------------------------------------------
# ABCWork tests
# ---------------------------------------------------------------------------


class TestABCWork:
    def test_required_fields(self):
        w = make_abc_work()
        assert w.code == "W-001"
        assert w.name == "Earthwork"
        assert w.unit == "м3"
        assert w.quantity == 100.0

    def test_optional_fields_default_none(self):
        w = make_abc_work()
        assert w.unit_price is None
        assert w.total_price is None
        assert w.chapter is None
        assert w.section is None

    def test_with_pricing(self):
        w = make_abc_work(unit_price=1500.0, total_price=150_000.0)
        assert w.unit_price == 1500.0
        assert w.total_price == 150_000.0

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            ABCWork(code="W-001", name="X", quantity=10.0)  # unit missing


# ---------------------------------------------------------------------------
# ABCMaterial tests
# ---------------------------------------------------------------------------


class TestABCMaterial:
    def test_required_fields(self):
        m = make_abc_material()
        assert m.code == "M-001"
        assert m.unit == "кг"
        assert m.quantity == 500.0

    def test_optional_supplier(self):
        m = make_abc_material(supplier="ТОО Стройснаб")
        assert m.supplier == "ТОО Стройснаб"

    def test_defaults_none(self):
        m = make_abc_material()
        assert m.supplier is None
        assert m.unit_price is None


# ---------------------------------------------------------------------------
# ResourceStatement tests
# ---------------------------------------------------------------------------


class TestResourceStatement:
    def test_minimal_creation(self):
        rs = ResourceStatement(name="Ресурсная ведомость №1")
        assert rs.name == "Ресурсная ведомость №1"
        assert rs.works == []
        assert rs.materials == []
        assert rs.id is None
        assert rs.total_cost is None

    def test_with_works_and_materials(self):
        rs = ResourceStatement(
            name="RS-1",
            works=[make_abc_work()],
            materials=[make_abc_material()],
            total_cost=250_000.0,
        )
        assert len(rs.works) == 1
        assert len(rs.materials) == 1
        assert rs.total_cost == 250_000.0

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            ResourceStatement()


# ---------------------------------------------------------------------------
# EstimatePosition tests
# ---------------------------------------------------------------------------


class TestEstimatePosition:
    def test_work_type(self):
        pos = EstimatePosition(
            position_number=1,
            code="W-001",
            name="Рытьё котлована",
            unit="м3",
            quantity=50.0,
            unit_price=2000.0,
            total_price=100_000.0,
            type="work",
        )
        assert pos.type == "work"
        assert pos.total_price == 100_000.0

    def test_material_type(self):
        pos = EstimatePosition(
            position_number=2,
            code="M-001",
            name="Цемент",
            unit="кг",
            quantity=200.0,
            unit_price=500.0,
            total_price=100_000.0,
            type="material",
        )
        assert pos.type == "material"

    def test_machine_type(self):
        pos = EstimatePosition(
            position_number=3,
            code="MC-001",
            name="Экскаватор",
            unit="маш-ч",
            quantity=8.0,
            unit_price=25_000.0,
            total_price=200_000.0,
            type="machine",
        )
        assert pos.type == "machine"

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            EstimatePosition(
                position_number=1,
                code="X",
                name="X",
                unit="шт",
                quantity=1.0,
                unit_price=100.0,
                total_price=100.0,
                type="invalid",
            )


# ---------------------------------------------------------------------------
# API Schemas tests
# ---------------------------------------------------------------------------


class TestTaskRequest:
    def test_minimal(self):
        req = TaskRequest(task_description="Найти тендеры в Алматы")
        assert req.task_description == "Найти тендеры в Алматы"
        assert req.region is None
        assert req.work_type is None
        assert req.budget_max is None

    def test_full(self):
        req = TaskRequest(
            task_description="Тендеры",
            region="Алматы",
            work_type="road",
            budget_max=10_000_000.0,
        )
        assert req.region == "Алматы"
        assert req.budget_max == 10_000_000.0

    def test_missing_description_raises(self):
        with pytest.raises(ValidationError):
            TaskRequest()


class TestTaskResponse:
    def test_creation(self):
        resp = TaskResponse(
            task_id="uuid-123",
            status=TaskStatusEnum.PENDING,
            created_at=NOW,
        )
        assert resp.task_id == "uuid-123"
        assert resp.status == TaskStatusEnum.PENDING
        assert resp.message == ""

    def test_all_statuses(self):
        for status in TaskStatusEnum:
            resp = TaskResponse(task_id="x", status=status, created_at=NOW)
            assert resp.status == status


class TestTaskStatus:
    def test_defaults(self):
        ts = TaskStatus(task_id="x", status=TaskStatusEnum.RUNNING, updated_at=NOW)
        assert ts.progress_pct == 0
        assert ts.current_agent is None
        assert ts.result is None
        assert ts.errors == []

    def test_progress_boundaries(self):
        ts = TaskStatus(task_id="x", status=TaskStatusEnum.RUNNING, updated_at=NOW, progress_pct=100)
        assert ts.progress_pct == 100

    def test_invalid_progress_raises(self):
        with pytest.raises(ValidationError):
            TaskStatus(task_id="x", status=TaskStatusEnum.RUNNING, updated_at=NOW, progress_pct=101)


class TestAgentReport:
    def test_defaults(self):
        report = AgentReport(task_id="x", created_at=NOW)
        assert report.tenders_found == 0
        assert report.selected_tender is None
        assert report.resource_statement is None
        assert report.purchase_orders == []
        assert report.total_budget_estimate is None
        assert report.execution_time_seconds is None

    def test_full_report(self):
        report = AgentReport(
            task_id="x",
            tenders_found=5,
            selected_tender={"id": "t-1", "name": "Road repair"},
            purchase_orders=[{"id": "po-1"}],
            total_budget_estimate=1_500_000.0,
            execution_time_seconds=42.5,
            created_at=NOW,
        )
        assert report.tenders_found == 5
        assert report.total_budget_estimate == 1_500_000.0
        assert len(report.purchase_orders) == 1


# ---------------------------------------------------------------------------
# ConstructionState tests
# ---------------------------------------------------------------------------


class TestConstructionState:
    def test_minimal_creation_with_task(self):
        state = ConstructionState(task="Найти тендеры на строительство дороги")
        assert state["task"] == "Найти тендеры на строительство дороги"

    def test_empty_creation(self):
        # total=False means all fields are optional
        state = ConstructionState()
        assert isinstance(state, dict)

    def test_full_state(self):
        tender = make_tender()
        work = make_abc_work()
        material = make_abc_material()
        state = ConstructionState(
            task="Test task",
            tenders=[tender],
            selected_tender=tender,
            work_list=[work],
            materials_list=[material],
            stock_check={"M-001": 200.0},
            purchase_orders=[{"id": "po-1"}],
            current_agent="procurement",
            errors=[],
            metadata={"trace_id": "abc123", "started_at": "2026-03-02"},
        )
        assert len(state["tenders"]) == 1
        assert state["selected_tender"].id == "t-1"
        assert state["current_agent"] == "procurement"
        assert state["stock_check"]["M-001"] == 200.0

    def test_messages_field_accepts_langchain_messages(self):
        msg = HumanMessage(content="Найди тендеры в Алматы")
        state = ConstructionState(task="test", messages=[msg])
        assert len(state["messages"]) == 1
        assert state["messages"][0].content == "Найди тендеры в Алматы"

    def test_state_is_dict_subtype(self):
        state = ConstructionState(task="test")
        assert isinstance(state, dict)
        assert "task" in state

    def test_errors_field(self):
        state = ConstructionState(task="test", errors=["API timeout", "Validation failed"])
        assert len(state["errors"]) == 2
        assert "API timeout" in state["errors"]
