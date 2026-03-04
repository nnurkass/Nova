"""Smoke test: full graph traversal with stub nodes, no LLM or DB required."""
from nova.graph.main_graph import build_graph


def _initial_state():
    return {
        "task": "Найди тендеры на строительство в Алматы",
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


def test_graph_builds_successfully():
    graph = build_graph()
    assert graph is not None


def test_graph_runs_through_all_stub_nodes():
    graph = build_graph()
    result = graph.invoke(_initial_state())
    assert result["current_agent"] == "supply"
    assert result["errors"] == []


def test_graph_returns_full_state():
    graph = build_graph()
    result = graph.invoke(_initial_state())
    assert "task" in result
    assert "messages" in result
