"""
Supply Agent (Отдел материально-технического снабжения).

Verifies inventory against the warehouse database, calculates deficit with +10%
safety stock, selects suppliers, flags URGENT orders, and passes the procurement
package to the COO.
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage

from nova.agents.level2.supply.prompts import SUPPLY_SYSTEM_PROMPT
from nova.agents.level3.order_tool import (
    build_purchase_orders_from_stock_check,
    create_purchase_order,
)
from nova.agents.level3.stock_tool import batch_check_stock, check_stock
from nova.agents.level3.supplier_tool import find_supplier
from nova.config import get_settings
from nova.graph.routers import ROUTE_COMPLETE
from nova.graph.state import ConstructionState

logger = logging.getLogger(__name__)

SUPPLY_TOOLS = [
    check_stock,
    create_purchase_order,
    find_supplier,
]


def create_supply_agent():
    """Create a LangChain ReAct agent for Supply when live LLM is configured."""
    try:
        from langgraph.prebuilt import create_react_agent
        from nova.config.llm import get_chat_model

        llm = get_chat_model(temperature=0.1, max_tokens=4096)
        if llm is None:
            return None

        return create_react_agent(llm, SUPPLY_TOOLS, prompt=SUPPLY_SYSTEM_PROMPT)
    except Exception as exc:
        logger.debug("Live Supply LLM agent initialization skipped: %s", exc)
        return None


def run_supply_agent(state: ConstructionState) -> dict[str, Any]:
    """Execute Supply agent logic: warehouse check, deficit calculation, PO generation."""
    metadata = dict(state.get("metadata", {}))
    visited = list(metadata.get("visited_nodes", []))
    visited.append("supply")
    metadata["visited_nodes"] = visited
    metadata["supply_completed"] = True

    materials = state.get("materials_list", [])
    materials_dicts = [
        m.model_dump() if hasattr(m, "model_dump") else dict(m)
        for m in materials
    ]

    # Batch stock verification against warehouse_mock
    stock_check = batch_check_stock(materials_dicts)

    # Determine delivery target region
    selected_tender = state.get("selected_tender")
    target_city = "Алматы"
    if selected_tender:
        t_text = (selected_tender.name_ru + " " + selected_tender.organizer_name_ru).lower()
        if "астан" in t_text:
            target_city = "Астана"
        elif "шымкент" in t_text:
            target_city = "Шымкент"
        elif "караганд" in t_text:
            target_city = "Караганда"

    # Build purchase orders with +10% safety buffer
    purchase_orders = build_purchase_orders_from_stock_check(
        stock_check.get("items", {}),
        target_city=target_city,
    )

    total_purchase_kzt = sum(po.get("total_amount_kzt", 0.0) for po in purchase_orders)
    urgent_count = sum(1 for po in purchase_orders if po.get("priority") == "URGENT")
    summary = stock_check.get("summary", {})

    summary_msg = (
        f"[СНАБЖЕНИЕ] Сверка со складом завершена. "
        f"Позиций проверено: {summary.get('total_items', 0)} "
        f"(в наличии: {summary.get('fully_in_stock', 0)}, "
        f"частично: {summary.get('partial_stock', 0)}, "
        f"дефицит: {summary.get('full_deficit', 0)}). "
        f"Сформировано заявок на закупку: {len(purchase_orders)} "
        f"(из них URGENT: {urgent_count}) с учетом страхового запаса +10%. "
        f"Общая сумма к закупке: {total_purchase_kzt:,.2f} KZT. "
        f"Передаю итоговую сводку COO для финального утверждения."
    )

    return {
        "stock_check": stock_check,
        "purchase_orders": purchase_orders,
        "current_agent": ROUTE_COMPLETE,
        "messages": [AIMessage(content=summary_msg, name="SupplyAgent")],
        "metadata": metadata,
    }


__all__ = [
    "create_supply_agent",
    "run_supply_agent",
    "SUPPLY_TOOLS",
]
