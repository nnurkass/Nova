"""Smoke tests for the Step 1.5 graph skeleton."""
from __future__ import annotations

from nova.graph.main_graph import build_graph


def test_graph_smoke_runs_through_all_stub_nodes(initial_construction_state):
    graph = build_graph()

    result = graph.invoke(initial_construction_state)

    assert result["metadata"]["visited_nodes"] == ["coo", "procurement", "pto", "supply"]
    assert result["current_agent"] == "complete"
    assert result["selected_tender"] is not None
    assert result["work_list"]
    assert result["materials_list"]
    assert result["stock_check"]
    assert result["purchase_orders"]
    assert result["errors"] == []
