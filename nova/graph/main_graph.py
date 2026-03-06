"""Main LangGraph skeleton for the Nova procurement pipeline."""
from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from nova.graph.routers import (
    ROUTE_COO,
    ROUTE_COMPLETE,
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
from nova.integrations.goszakup.models import Tender, TenderLot


def _copy_metadata(state: ConstructionState, node_name: str) -> dict[str, Any]:
    metadata = dict(state["metadata"])
    visited_nodes = list(metadata.get("visited_nodes", []))
    visited_nodes.append(node_name)
    metadata["visited_nodes"] = visited_nodes
    return metadata


def _build_stub_tender(task: str) -> Tender:
    return Tender(
        id=1,
        number="STUB-2026-001",
        name_ru=f"Тендер по задаче: {task}",
        status_id=1,
        trd_buy_type_id=1,
        organizer_id=1,
        organizer_bin="123456789012",
        organizer_name_ru="Тестовый организатор",
        total_sum=25_000_000.0,
        lots=[
            TenderLot(
                id=1,
                lot_number=1,
                name_ru="Строительно-монтажные работы",
                amount=1.0,
                unit="услуга",
            )
        ],
    )


def coo_node(state: ConstructionState) -> dict[str, Any]:
    """Delegate the task to procurement as the first Level 2 agent."""
    return {
        "current_agent": ROUTE_PROCUREMENT,
        "metadata": _copy_metadata(state, ROUTE_COO),
    }


def procurement_node(state: ConstructionState) -> dict[str, Any]:
    """Create a stub tender selection for downstream graph nodes."""
    metadata = _copy_metadata(state, ROUTE_PROCUREMENT)
    tender = state["selected_tender"] or _build_stub_tender(state["task"])
    tenders = list(state["tenders"]) or [tender]

    return {
        "tenders": tenders,
        "selected_tender": tender,
        "current_agent": ROUTE_PTO,
        "metadata": metadata,
    }


def pto_node(state: ConstructionState) -> dict[str, Any]:
    """Produce a minimal work/material package for the supply agent."""
    metadata = _copy_metadata(state, ROUTE_PTO)
    work_list = list(state["work_list"]) or [
        ABCWork(code="6.1.2-1.1", name="Земляные работы", unit="м3", quantity=150.0)
    ]
    materials_list = list(state["materials_list"]) or [
        ABCMaterial(code="245-1234", name="Арматура А500С", unit="т", quantity=5.5)
    ]

    return {
        "work_list": work_list,
        "materials_list": materials_list,
        "current_agent": ROUTE_SUPPLY,
        "metadata": metadata,
    }


def supply_node(state: ConstructionState) -> dict[str, Any]:
    """Generate stub stock-check and purchase order outputs."""
    metadata = _copy_metadata(state, ROUTE_SUPPLY)
    metadata["supply_completed"] = True
    stock_check = dict(state["stock_check"]) or {
        "245-1234": {
            "name": "Арматура А500С",
            "required": 5.5,
            "in_stock": 2.0,
            "to_purchase": 3.5,
        }
    }
    purchase_orders = list(state["purchase_orders"]) or [
        {
            "item_code": "245-1234",
            "name": "Арматура А500С",
            "quantity": 3.5,
            "unit": "т",
        }
    ]

    return {
        "stock_check": stock_check,
        "purchase_orders": purchase_orders,
        "current_agent": ROUTE_COMPLETE,
        "metadata": metadata,
    }


def build_graph():
    """Compile and return the Step 1.5 skeleton graph."""
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

    return workflow.compile(name="nova_main_graph")
