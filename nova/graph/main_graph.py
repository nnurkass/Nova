"""
Main LangGraph graph for the Nova pipeline. Implemented in Step 1.5 (skeleton).

Stub nodes pass state through unchanged; real agents are wired in Step 4.2.
Conditional routing (routers.py) is connected in Step 4.2.
"""
from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from nova.graph.state import ConstructionState


# ---------------------------------------------------------------------------
# Stub nodes — just mark which agent ran; replaced in Step 3.x / 4.x
# ---------------------------------------------------------------------------

def _coo_node(state: ConstructionState) -> dict[str, Any]:
    return {"current_agent": "coo"}


def _procurement_node(state: ConstructionState) -> dict[str, Any]:
    return {"current_agent": "procurement"}


def _pto_node(state: ConstructionState) -> dict[str, Any]:
    return {"current_agent": "pto"}


def _supply_node(state: ConstructionState) -> dict[str, Any]:
    return {"current_agent": "supply"}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(checkpointer=None):
    """Build and compile the Nova LangGraph pipeline.

    Args:
        checkpointer: Optional LangGraph checkpointer (e.g. MemorySaver).
                      Pass None (default) for stateless invocations.

    Returns:
        Compiled LangGraph CompiledGraph.
    """
    builder = StateGraph(ConstructionState)

    builder.add_node("coo", _coo_node)
    builder.add_node("procurement", _procurement_node)
    builder.add_node("pto", _pto_node)
    builder.add_node("supply", _supply_node)

    builder.set_entry_point("coo")

    # Sequential edges for skeleton; conditional routing added in Step 4.2
    builder.add_edge("coo", "procurement")
    builder.add_edge("procurement", "pto")
    builder.add_edge("pto", "supply")
    builder.add_edge("supply", END)

    return builder.compile(checkpointer=checkpointer)
