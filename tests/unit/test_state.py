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

    def test_tender_lots_default_is_not_shared(self):
        from nova.integrations.goszakup.models import Tender, TenderLot
        first = Tender(
            id=100,
            number="АНО-2026-001",
            name_ru="Строительство дороги",
            status_id=1,
            trd_buy_type_id=2,
            organizer_id=10,
            organizer_bin="123456789012",
            organizer_name_ru="АО Тест",
        )
        second = Tender(
            id=101,
            number="АНО-2026-002",
            name_ru="Строительство моста",
            status_id=1,
            trd_buy_type_id=2,
            organizer_id=10,
            organizer_bin="123456789012",
            organizer_name_ru="АО Тест",
        )
        first.lots.append(TenderLot(id=1, lot_number=1, name_ru="Лот 1"))
        assert second.lots == []

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


# ── 1.3.3  ABC models ─────────────────────────────────────────────────
class TestABCModels:
    def test_abc_work_creation(self):
        from nova.integrations.abc.models import ABCWork
        work = ABCWork(code="6.1.2-1.1", name="Земляные работы", unit="м3", quantity=150.0)
        assert work.code == "6.1.2-1.1"
        assert work.price is None

    def test_abc_material_creation(self):
        from nova.integrations.abc.models import ABCMaterial
        mat = ABCMaterial(code="245-1234", name="Арматура А500С", unit="т", quantity=5.5)
        assert mat.quantity == 5.5
        assert mat.price is None

    def test_resource_statement_defaults(self):
        from nova.integrations.abc.models import ResourceStatement
        stmt = ResourceStatement()
        assert stmt.works == []
        assert stmt.materials == []
        assert stmt.tender_id is None

    def test_resource_statement_defaults_are_not_shared(self):
        from nova.integrations.abc.models import ResourceStatement, ABCWork
        first = ResourceStatement()
        second = ResourceStatement()
        first.works.append(ABCWork(code="1", name="Работа", unit="м3", quantity=1.0))
        assert second.works == []

    def test_estimate_position_is_work_flag(self):
        from nova.integrations.abc.models import EstimatePosition
        pos = EstimatePosition(
            position_number=1,
            code="6.1.2-1.1",
            name="Земляные работы",
            unit="м3",
            quantity=100.0,
            is_work=True,
        )
        assert pos.is_work is True
        assert pos.unit_price is None


# ── 1.3.4  API schemas ────────────────────────────────────────────────
class TestAPISchemas:
    def test_task_request_requires_task(self):
        import pytest
        from pydantic import ValidationError
        from nova.api.schemas import TaskRequest
        with pytest.raises(ValidationError):
            TaskRequest()  # task is required

    def test_task_request_creation(self):
        from nova.api.schemas import TaskRequest
        req = TaskRequest(task="Найти тендер на строительство в Алматы")
        assert req.task == "Найти тендер на строительство в Алматы"
        assert req.region is None
        assert req.budget_max is None

    def test_task_status_enum_values(self):
        from nova.api.schemas import TaskStatusEnum
        assert TaskStatusEnum.PENDING == "pending"
        assert TaskStatusEnum.RUNNING == "running"
        assert TaskStatusEnum.COMPLETED == "completed"
        assert TaskStatusEnum.FAILED == "failed"

    def test_task_response_has_uuid(self):
        from uuid import UUID
        from nova.api.schemas import TaskResponse, TaskStatusEnum
        from datetime import datetime, timezone
        resp = TaskResponse(
            task_id=UUID("12345678-1234-5678-1234-567812345678"),
            status=TaskStatusEnum.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        assert isinstance(resp.task_id, UUID)

    def test_agent_report_defaults(self):
        from uuid import UUID
        from datetime import datetime, timezone
        from nova.api.schemas import AgentReport
        report = AgentReport(
            task_id=UUID("12345678-1234-5678-1234-567812345678"),
            task="тест",
            recommendations="Рекомендуется участвовать",
            created_at=datetime.now(timezone.utc),
        )
        assert report.purchase_orders == []
        assert report.selected_tender is None

    def test_agent_report_purchase_orders_default_is_not_shared(self):
        from uuid import UUID
        from datetime import datetime, timezone
        from nova.api.schemas import AgentReport
        first = AgentReport(
            task_id=UUID("12345678-1234-5678-1234-567812345678"),
            task="тест",
            recommendations="ok",
            created_at=datetime.now(timezone.utc),
        )
        second = AgentReport(
            task_id=UUID("87654321-4321-8765-4321-876543218765"),
            task="тест",
            recommendations="ok",
            created_at=datetime.now(timezone.utc),
        )
        first.purchase_orders.append({"item": "cement"})
        assert second.purchase_orders == []


# ── 1.3.1  ConstructionState ──────────────────────────────────────────
class TestConstructionState:
    def test_state_creation_minimal(self):
        from nova.graph.state import ConstructionState
        state: ConstructionState = {
            "task": "найти тендер на строительство",
            "tenders": [],
            "selected_tender": None,
            "work_list": [],
            "materials_list": [],
            "stock_check": {},
            "purchase_orders": [],
            "current_agent": "",
            "messages": [],
            "errors": [],
            "metadata": {},
        }
        assert state["task"] == "найти тендер на строительство"
        assert state["messages"] == []

    def test_state_messages_field_type(self):
        """messages field uses add_messages reducer — verify annotation exists."""
        import typing
        from nova.graph.state import ConstructionState
        hints = typing.get_type_hints(ConstructionState, include_extras=True)
        assert "messages" in hints
        # Annotated type has __metadata__
        assert hasattr(hints["messages"], "__metadata__")

    def test_state_with_tender(self):
        from nova.graph.state import ConstructionState
        from nova.integrations.goszakup.models import Tender
        tender = Tender(
            id=1, number="АНО-001", name_ru="Тест",
            status_id=1, trd_buy_type_id=1,
            organizer_id=1, organizer_bin="000000000000",
            organizer_name_ru="Тест Орг",
        )
        state: ConstructionState = {
            "task": "тест",
            "tenders": [tender],
            "selected_tender": tender,
            "work_list": [],
            "materials_list": [],
            "stock_check": {},
            "purchase_orders": [],
            "current_agent": "procurement",
            "messages": [],
            "errors": [],
            "metadata": {"started_at": "2026-03-03"},
        }
        assert len(state["tenders"]) == 1
        assert state["current_agent"] == "procurement"

    def test_messages_accumulate_with_reducer(self):
        """Simulate LangGraph's add_messages reducer behaviour."""
        from langchain_core.messages import HumanMessage, AIMessage
        from langgraph.graph.message import add_messages
        msgs: list = []
        msgs = add_messages(msgs, [HumanMessage(content="hello")])
        msgs = add_messages(msgs, [AIMessage(content="world")])
        assert len(msgs) == 2
        assert msgs[0].content == "hello"
