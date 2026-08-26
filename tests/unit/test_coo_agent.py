"""Unit tests for COO Agent and Executive Summary generator."""
from nova.agents.coo.agent import generate_executive_summary, run_coo_agent
from nova.graph.state import ConstructionState
from nova.integrations.abc.models import ABCMaterial, ABCWork
from nova.integrations.goszakup.models import Tender, TenderLot


def _sample_completed_state() -> ConstructionState:
    tender = Tender(
        id=10123456,
        number="10123456-1",
        name_ru="Капитальный ремонт школы №12",
        status_id=1,
        trd_buy_type_id=2,
        organizer_id=1,
        organizer_bin="990140001234",
        organizer_name_ru="Управление образования г. Алматы",
        total_sum=185_000_000.0,
        lots=[TenderLot(id=1, lot_number=1, name_ru="СМР", amount=185_000_000.0, count=1.0, unit="усл")],
    )
    work_list = [
        ABCWork(code="ВОР-01", name="Демонтажные работы", unit="м2", quantity=1000.0),
        ABCWork(code="ВОР-02", name="Отделочные работы", unit="м2", quantity=1500.0),
    ]
    materials_list = [
        ABCMaterial(code="245-1012", name="Арматура А500С d12мм", unit="т", quantity=10.0, price=320000.0),
        ABCMaterial(code="101-0300", name="Бетон товарный М300 В22.5", unit="м3", quantity=50.0, price=28500.0),
    ]
    stock_check = {
        "items": {
            "245-1012": {"code": "245-1012", "name": "Арматура А500С", "required": 10.0, "available": 4.0, "deficit": 6.0},
            "101-0300": {"code": "101-0300", "name": "Бетон товарный М300", "required": 50.0, "available": 0.0, "deficit": 50.0},
        },
        "summary": {
            "total_items": 2,
            "fully_in_stock": 0,
            "partial_stock": 1,
            "full_deficit": 1,
            "total_required_cost": 4625000.0,
            "in_stock_covered_value": 1280000.0,
            "to_purchase_estimated_cost": 3345000.0,
        },
    }
    purchase_orders = [
        {
            "order_id": "PO-2026-001",
            "name": "Арматура А500С",
            "required_quantity": 10.0,
            "order_quantity": 6.6,
            "unit": "т",
            "total_amount_kzt": 2112000.0,
            "priority": "NORMAL",
            "supplier_name": "ТОО «КазАрматура Трейд»",
        },
        {
            "order_id": "PO-2026-002",
            "name": "Бетон товарный М300",
            "required_quantity": 50.0,
            "order_quantity": 55.0,
            "unit": "м3",
            "total_amount_kzt": 1540000.0,
            "priority": "URGENT",
            "supplier_name": "ТОО «АзияБетон Плюс»",
        },
    ]
    return {
        "task": "Поиск тендеров на капремонт школ в г. Алматы",
        "tenders": [tender],
        "selected_tender": tender,
        "work_list": work_list,
        "materials_list": materials_list,
        "stock_check": stock_check,
        "purchase_orders": purchase_orders,
        "current_agent": "complete",
        "messages": [],
        "errors": [],
        "metadata": {"visited_nodes": ["coo", "procurement", "pto", "supply"], "supply_completed": True},
    }


class TestCOOAgent:
    def test_coo_initial_dispatch(self):
        state: ConstructionState = {
            "task": "Найти тендер на строительство школы в Астане",
            "tenders": [],
            "selected_tender": None,
            "work_list": [],
            "materials_list": [],
            "stock_check": {},
            "purchase_orders": [],
            "current_agent": "coo",
            "messages": [],
            "errors": [],
            "metadata": {},
        }
        res = run_coo_agent(state)
        assert res["current_agent"] == "procurement"
        assert len(res["messages"]) == 1
        assert "procurement" == res["current_agent"]

    def test_generate_executive_summary(self):
        state = _sample_completed_state()
        report = generate_executive_summary(state)

        assert "# 🏗️ NOVA — ИСПОЛНИТЕЛЬНЫЙ ОТЧЁТ" in report
        assert "10123456-1" in report
        assert "185,000,000" in report
        assert "ИНЖЕНЕРНАЯ ВЕДОМОСТЬ" in report
        assert "СКЛАДСКОЙ БАЛАНС" in report
        assert "ФИНАНСОВЫЙ БАЛАНС" in report
        assert "ТОО «КазАрматура Трейд»" in report

    def test_coo_final_synthesis(self):
        state = _sample_completed_state()
        res = run_coo_agent(state)

        assert res["current_agent"] == "end"
        assert "final_report" in res["metadata"]
        assert len(res["metadata"]["final_report"]) > 100
