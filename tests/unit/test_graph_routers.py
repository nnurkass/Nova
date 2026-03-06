"""Unit tests for graph routing helpers."""
from __future__ import annotations

from nova.graph.routers import (
    ROUTE_COO,
    ROUTE_END,
    ROUTE_PROCUREMENT,
    ROUTE_PTO,
    ROUTE_SUPPLY,
    is_complete,
    route_after_coo,
    route_after_procurement,
    should_continue,
)
from nova.graph.state import ConstructionState
from nova.integrations.abc.models import ABCMaterial, ABCWork
from nova.integrations.goszakup.models import Tender


def make_state(**overrides) -> ConstructionState:
    state: ConstructionState = {
        "task": "Тестовая задача",
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
    state.update(overrides)
    return state


class TestRouteAfterCoo:
    def test_routes_to_procurement(self):
        state = make_state(current_agent=ROUTE_PROCUREMENT)
        assert route_after_coo(state) == ROUTE_PROCUREMENT

    def test_routes_to_supply(self):
        state = make_state(current_agent=ROUTE_SUPPLY)
        assert route_after_coo(state) == ROUTE_SUPPLY

    def test_ends_when_errors_exist(self):
        state = make_state(current_agent=ROUTE_PROCUREMENT, errors=["boom"])
        assert route_after_coo(state) == ROUTE_END

    def test_ends_when_agent_is_unknown(self):
        state = make_state(current_agent="unknown")
        assert route_after_coo(state) == ROUTE_END


class TestRouteAfterProcurement:
    def test_routes_to_pto_when_tender_selected(self):
        tender = Tender(
            id=1,
            number="ANO-1",
            name_ru="Тестовый тендер",
            status_id=1,
            trd_buy_type_id=1,
            organizer_id=1,
            organizer_bin="123456789012",
            organizer_name_ru="Тестовый организатор",
        )
        state = make_state(selected_tender=tender)
        assert route_after_procurement(state) == ROUTE_PTO

    def test_ends_when_no_tender_was_selected(self):
        state = make_state()
        assert route_after_procurement(state) == ROUTE_END


class TestShouldContinue:
    def test_routes_to_supply_when_work_is_ready(self):
        work = ABCWork(code="1", name="Земляные работы", unit="м3", quantity=10)
        state = make_state(work_list=[work])
        assert should_continue(state) == ROUTE_SUPPLY

    def test_routes_to_supply_when_materials_are_ready(self):
        material = ABCMaterial(code="2", name="Бетон", unit="м3", quantity=5)
        state = make_state(materials_list=[material])
        assert should_continue(state) == ROUTE_SUPPLY

    def test_ends_when_pto_has_errors(self):
        work = ABCWork(code="1", name="Земляные работы", unit="м3", quantity=10)
        state = make_state(work_list=[work], errors=["pto failed"])
        assert should_continue(state) == ROUTE_END


class TestIsComplete:
    def test_ends_when_supply_outputs_are_ready(self):
        state = make_state(
            stock_check={"cement": {"in_stock": 10}},
            purchase_orders=[{"item": "cement", "quantity": 5}],
        )
        assert is_complete(state) == ROUTE_END

    def test_returns_to_coo_when_outputs_are_missing(self):
        state = make_state(stock_check={"cement": {"in_stock": 10}})
        assert is_complete(state) == ROUTE_COO
