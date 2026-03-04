"""Unit tests for LangGraph routing functions."""
from nova.graph.routers import route_after_coo, route_after_procurement, should_continue, is_complete


def _state(**kwargs):
    base = {
        "task": "test", "tenders": [], "selected_tender": None,
        "work_list": [], "materials_list": [], "stock_check": {},
        "purchase_orders": [], "current_agent": "", "messages": [],
        "errors": [], "metadata": {},
    }
    base.update(kwargs)
    return base


def test_route_after_coo_returns_procurement():
    assert route_after_coo(_state(current_agent="coo")) == "procurement"


def test_route_after_coo_errors_returns_end():
    assert route_after_coo(_state(errors=["oops"])) == "end"


def test_route_after_procurement_with_tender_returns_pto():
    from nova.integrations.goszakup.models import Tender
    tender = Tender(
        id=1, number="001", name_ru="Тест",
        status_id=1, trd_buy_type_id=1,
        organizer_id=1, organizer_bin="123456789012",
        organizer_name_ru="ТОО Тест",
    )
    assert route_after_procurement(_state(selected_tender=tender)) == "pto"


def test_route_after_procurement_no_tender_returns_end():
    assert route_after_procurement(_state(selected_tender=None)) == "end"


def test_should_continue_true():
    assert should_continue(_state()) is True


def test_should_continue_false_when_errors():
    assert should_continue(_state(errors=["fail"])) is False


def test_is_complete_true():
    assert is_complete(_state(current_agent="done")) is True


def test_is_complete_false():
    assert is_complete(_state()) is False
