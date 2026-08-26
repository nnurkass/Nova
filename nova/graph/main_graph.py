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
import time
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


def serialize_state_for_api(state: ConstructionState) -> dict[str, Any]:
    """Serialize graph state to pure JSON-compatible dictionary."""
    selected_tender = state.get("selected_tender")
    tenders = state.get("tenders", [])
    work_list = state.get("work_list", [])
    materials_list = state.get("materials_list", [])
    messages = state.get("messages", [])

    return {
        "task": state.get("task", ""),
        "selected_tender": selected_tender.model_dump(mode="json") if hasattr(selected_tender, "model_dump") else selected_tender,
        "tenders": [
            t.model_dump(mode="json") if hasattr(t, "model_dump") else t
            for t in tenders
        ],
        "work_list": [
            w.model_dump(mode="json") if hasattr(w, "model_dump") else w
            for w in work_list
        ],
        "materials_list": [
            m.model_dump(mode="json") if hasattr(m, "model_dump") else m
            for m in materials_list
        ],
        "stock_check": state.get("stock_check", {}),
        "purchase_orders": state.get("purchase_orders", []),
        "current_agent": state.get("current_agent", "end"),
        "messages": [
            {"content": m.content, "name": getattr(m, "name", "agent")} if hasattr(m, "content") else str(m)
            for m in messages
        ],
        "errors": list(state.get("errors", [])),
        "metadata": dict(state.get("metadata", {})),
        "executive_summary": state.get("metadata", {}).get("final_report") or state.get("metadata", {}).get("executive_summary", ""),
    }


def stream_pipeline(
    task: str,
    initial_state: Optional[dict[str, Any]] = None,
    delay: float = 0.0,
):
    """
    Generator yielding step-by-step agent execution events for real-time streaming.
    Yields event dictionaries with event type, agent node info, messages, and state snapshot.
    """
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

    # Initial start event
    yield {
        "event": "pipeline_start",
        "node": "coo",
        "step_index": 0,
        "total_steps": 5,
        "agent_title": "COO Supervisor",
        "message": f"Инициализация мульти-агентного анализа: «{task}»",
        "status": "running",
        "data": {},
        "state": serialize_state_for_api(state),
    }

    step_index = 0
    agent_titles = {
        "coo": "Операционный директор (COO)",
        "procurement": "Гос. Закупщик (Goszakup)",
        "pto": "Инженер ПТО (Сметы & Нормативы)",
        "supply": "Отдел снабжения (Склад & Закупки)",
    }

    for step_output in graph.stream(state):
        node_name = list(step_output.keys())[0]
        node_val = step_output[node_name]
        step_index += 1

        # Accumulate node output into running state
        state.update(node_val)

        # Extract latest message from this agent
        agent_msgs = node_val.get("messages", [])
        last_msg_text = agent_msgs[-1].content if agent_msgs and hasattr(agent_msgs[-1], "content") else ""

        # Extract structured data for this step
        step_data: dict[str, Any] = {}
        if node_name == "procurement":
            sel = state.get("selected_tender")
            step_data = {
                "tenders_found": len(state.get("tenders", [])),
                "selected_tender": sel.model_dump(mode="json") if hasattr(sel, "model_dump") else sel,
            }
        elif node_name == "pto":
            step_data = {
                "works_count": len(state.get("work_list", [])),
                "materials_count": len(state.get("materials_list", [])),
            }
        elif node_name == "supply":
            step_data = {
                "stock_summary": state.get("stock_check", {}).get("summary", {}),
                "purchase_orders_count": len(state.get("purchase_orders", [])),
            }

        yield {
            "event": "node_complete",
            "node": node_name,
            "step_index": step_index,
            "total_steps": 5,
            "agent_title": agent_titles.get(node_name, node_name.upper()),
            "message": last_msg_text,
            "status": "success" if not state.get("errors") else "error",
            "data": step_data,
            "state": serialize_state_for_api(state),
        }
        if delay > 0:
            time.sleep(delay)

    # Step 5: Final Executive Summary compilation
    if not state.get("errors") and state.get("metadata", {}).get("supply_completed"):
        report = generate_executive_summary(state)
        state["metadata"]["final_report"] = report
        state["metadata"]["executive_summary"] = report
        step_index += 1

        yield {
            "event": "node_complete",
            "node": "coo_summary",
            "step_index": step_index,
            "total_steps": 5,
            "agent_title": "COO — Исполнительный отчёт",
            "message": "Формирование финального Исполнительного Отчета (Executive Summary) и финансового баланса.",
            "status": "success",
            "data": {"executive_summary": report},
            "state": serialize_state_for_api(state),
        }
        if delay > 0:
            time.sleep(delay)

    # Pipeline Complete Event
    yield {
        "event": "pipeline_complete",
        "node": "complete",
        "step_index": 5,
        "total_steps": 5,
        "agent_title": "Мульти-агентный пайплайн завершен",
        "message": "Анализ успешно завершен. Все данные и заявки сформированы.",
        "status": "success" if not state.get("errors") else "failed",
        "data": {},
        "state": serialize_state_for_api(state),
    }


__all__ = [
    "build_graph",
    "run_pipeline",
    "stream_pipeline",
    "serialize_state_for_api",
    "coo_node",
    "procurement_node",
    "pto_node",
    "supply_node",
]

