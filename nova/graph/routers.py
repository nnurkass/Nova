"""Conditional routing functions for the LangGraph pipeline. Implemented in Step 1.5."""
from __future__ import annotations

from nova.graph.state import ConstructionState


def route_after_coo(state: ConstructionState) -> str:
    """After COO node: route to procurement or end on error."""
    if state.get("errors"):
        return "end"
    return "procurement"


def route_after_procurement(state: ConstructionState) -> str:
    """After Procurement node: proceed to PTO if tender selected, else end."""
    if state.get("errors"):
        return "end"
    if state.get("selected_tender") is not None:
        return "pto"
    return "end"


def should_continue(state: ConstructionState) -> bool:
    """Check if pipeline should keep running."""
    return not bool(state.get("errors")) and not is_complete(state)


def is_complete(state: ConstructionState) -> bool:
    """Check if pipeline has reached terminal state."""
    return bool(state.get("purchase_orders")) or state.get("current_agent") == "done"
