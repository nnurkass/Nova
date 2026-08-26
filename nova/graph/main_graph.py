"""
Main LangGraph pipeline for the Nova multi-agent construction procurement system.

Orchestrates:
- COO Agent (Task intake & Executive Summary synthesis)
- Procurement Agent (Goszakup search, scoring & lot selection)
- PTO Agent (Technical specification & BOQ extraction via ABC/SN RK)
- Supply Agent (Warehouse stock checking, deficit calculation & purchase order creation)
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from langgraph.graph import END, START, StateGraph

from nova.agents.coo.agent import generate_executive_summary, run_coo_agent
from nova.agents.level2.procurement.agent import run_procurement_agent
from nova.agents.level2.pto.agent import run_pto_agent
from nova.agents.level2.supply.agent import run_supply_agent
from nova.graph.routers import (
    ROUTE_COMPLETE,
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

logger = logging.getLogger(__name__)


def coo_node(state: ConstructionState) -> dict[str, Any]:
    """Execute COO supervisor node."""
    try:
        return run_coo_agent(state)
    except Exception as exc:
        logger.error("Error in coo_node: %s", exc)
        errors = list(state.get("errors", []))
        errors.append(f"COO Agent Error: {exc}")
        return {"errors": errors, "current_agent": ROUTE_END}


def procurement_node(state: ConstructionState) -> dict[str, Any]:
    """Execute Procurement agent node."""
    try:
        return run_procurement_agent(state)
    except Exception as exc:
        logger.error("Error in procurement_node: %s", exc)
        errors = list(state.get("errors", []))
        errors.append(f"Procurement Agent Error: {exc}")
        return {"errors": errors, "current_agent": ROUTE_END}


def pto_node(state: ConstructionState) -> dict[str, Any]:
    """Execute PTO technical analysis node."""
    try:
        return run_pto_agent(state)
    except Exception as exc:
        logger.error("Error in pto_node: %s", exc)
        errors = list(state.get("errors", []))
        errors.append(f"PTO Agent Error: {exc}")
        return {"errors": errors, "current_agent": ROUTE_END}


def supply_node(state: ConstructionState) -> dict[str, Any]:
    """Execute Supply & Inventory verification node."""
    try:
        return run_supply_agent(state)
    except Exception as exc:
        logger.error("Error in supply_node: %s", exc)
        errors = list(state.get("errors", []))
        errors.append(f"Supply Agent Error: {exc}")
        return {"errors": errors, "current_agent": ROUTE_END}


def build_graph():
    """Build and compile the multi-agent StateGraph."""
    workflow = StateGraph(ConstructionState)

    workflow.add_node(ROUTE_COO, coo_node)
    workflow.add_node(ROUTE_PROCUREMENT, procurement_node)
    workflow.add_node(ROUTE_PTO, pto_node)
    workflow.add_node(ROUTE_SUPPLY, supply_node)

    workflow.add_edge(START, ROUTE_COO)
    workflow.add_conditional_edges(
        ROUTE_COO,
        route_after_coo,
        {
            ROUTE_PROCUREMENT: ROUTE_PROCUREMENT,
            ROUTE_PTO: ROUTE_PTO,
            ROUTE_SUPPLY: ROUTE_SUPPLY,
            ROUTE_END: END,
        },
    )
    workflow.add_conditional_edges(
        ROUTE_PROCUREMENT,
        route_after_procurement,
        {
            ROUTE_PTO: ROUTE_PTO,
            ROUTE_END: END,
        },
    )
    workflow.add_conditional_edges(
        ROUTE_PTO,
        should_continue,
        {
            ROUTE_SUPPLY: ROUTE_SUPPLY,
            ROUTE_END: END,
        },
    )
    workflow.add_conditional_edges(
        ROUTE_SUPPLY,
        is_complete,
        {
            ROUTE_COO: ROUTE_COO,
            ROUTE_END: END,
        },
    )

    return workflow.compile(name="nova_procurement_graph")


def run_pipeline(
    task: str,
    initial_state: Optional[dict[str, Any]] = None,
) -> ConstructionState:
    """Run full procurement pipeline and generate final Executive Summary."""
    graph = build_graph()

    state: ConstructionState = {
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
        "metadata": {"visited_nodes": []},
    }
    if initial_state:
        state.update(initial_state)

    final_state: ConstructionState = graph.invoke(state)

    # Attach Executive Summary report
    if not final_state.get("errors") and final_state.get("metadata", {}).get("supply_completed"):
        report = generate_executive_summary(final_state)
        final_state["metadata"]["final_report"] = report
        final_state["metadata"]["executive_summary"] = report

    return final_state


__all__ = [
    "build_graph",
    "run_pipeline",
    "coo_node",
    "procurement_node",
    "pto_node",
    "supply_node",
]
