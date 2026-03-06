"""Conditional routing helpers for the LangGraph pipeline."""
from __future__ import annotations

from nova.graph.state import ConstructionState


ROUTE_END = "end"
ROUTE_COO = "coo"
ROUTE_COMPLETE = "complete"
ROUTE_PROCUREMENT = "procurement"
ROUTE_PTO = "pto"
ROUTE_SUPPLY = "supply"

_VALID_COO_ROUTES = {
    ROUTE_PROCUREMENT,
    ROUTE_PTO,
    ROUTE_SUPPLY,
}


def route_after_coo(state: ConstructionState) -> str:
    """Route COO output to the requested Level 2 agent or finish early."""
    if state["errors"]:
        return ROUTE_END

    next_agent = state["current_agent"].strip().lower()
    if next_agent in _VALID_COO_ROUTES:
        return next_agent
    return ROUTE_END


def route_after_procurement(state: ConstructionState) -> str:
    """Continue to PTO only when procurement selected a tender."""
    if state["errors"]:
        return ROUTE_END
    if state["selected_tender"] is not None:
        return ROUTE_PTO
    return ROUTE_END


def should_continue(state: ConstructionState) -> str:
    """Proceed to supply once PTO produced works or materials."""
    if state["errors"]:
        return ROUTE_END
    if state["work_list"] or state["materials_list"]:
        return ROUTE_SUPPLY
    return ROUTE_END


def is_complete(state: ConstructionState) -> str:
    """Finish when supply produced the final artifacts; otherwise loop to COO."""
    if state["errors"]:
        return ROUTE_END
    if state["current_agent"] == ROUTE_COMPLETE or state["metadata"].get("supply_completed"):
        return ROUTE_END
    return ROUTE_COO
