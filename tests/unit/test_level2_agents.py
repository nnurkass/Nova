"""Unit tests for Level 2 agents: Procurement, PTO, and Supply."""
from nova.agents.level2.procurement.agent import run_procurement_agent
from nova.agents.level2.pto.agent import run_pto_agent
from nova.agents.level2.supply.agent import run_supply_agent
from nova.graph.state import ConstructionState
from nova.integrations.abc.models import ABCMaterial, ABCWork
from nova.integrations.goszakup.models import Tender, TenderLot


def _base_state(task: str = "Поиск тендеров на капремонт школ в г. Алматы") -> ConstructionState:
    return {
        "task": task,
        "tenders": [],
        "selected_tender": None,
        "work_list": [],
        "materials_list": [],
        "stock_check": {},
        "purchase_orders": [],
        "current_agent": "coo",
        "messages": [],
        "errors": [],
        "metadata": {"visited_nodes": ["coo"]},
    }


class TestLevel2Agents:
    def test_procurement_agent_run(self):
        state = _base_state()
        result = run_procurement_agent(state)

        assert "tenders" in result
        assert len(result["tenders"]) > 0
        assert result["selected_tender"] is not None
        assert isinstance(result["selected_tender"], Tender)
        assert result["current_agent"] == "pto"
        assert len(result["messages"]) > 0
        assert "procurement" in result["metadata"]["visited_nodes"]

    def test_pto_agent_run(self):
        state = _base_state()
        state["selected_tender"] = Tender(
            id=10123456,
            number="10123456-1",
            name_ru="Капитальный ремонт школы №12",
            status_id=1,
            trd_buy_type_id=2,
            organizer_id=1,
            organizer_bin="990140001234",
            organizer_name_ru="Управление образования",
            total_sum=185000000.0,
            lots=[TenderLot(id=1, lot_number=1, name_ru="СМР", amount=185000000.0, count=1.0, unit="усл")],
        )
        result = run_pto_agent(state)

        assert "work_list" in result
        assert len(result["work_list"]) > 0
        assert all(isinstance(w, ABCWork) for w in result["work_list"])

        assert "materials_list" in result
        assert len(result["materials_list"]) > 0
        assert all(isinstance(m, ABCMaterial) for m in result["materials_list"])
        assert result["current_agent"] == "supply"

    def test_supply_agent_run(self):
        state = _base_state()
        state["materials_list"] = [
            ABCMaterial(code="245-1012", name="Арматура А500С d12мм", unit="т", quantity=10.0, price=320000.0),
            ABCMaterial(code="101-0300", name="Бетон товарный М300 В22.5", unit="м3", quantity=50.0, price=28500.0),
        ]
        result = run_supply_agent(state)

        assert "stock_check" in result
        assert "items" in result["stock_check"]
        assert "purchase_orders" in result
        assert len(result["purchase_orders"]) > 0
        assert result["current_agent"] == "complete"
        assert result["metadata"].get("supply_completed") is True

        # Check safety buffer applied
        for po in result["purchase_orders"]:
            assert po["safety_buffer_pct"] == 10.0
            assert po["priority"] in {"URGENT", "NORMAL"}
            assert "total_amount_kzt" in po
