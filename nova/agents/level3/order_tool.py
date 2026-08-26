"""
LangChain tool for creating purchase orders with deficit and safety buffer calculation.

Generates structured procurement orders for missing construction materials,
applying a 10% safety stock reserve and supplier grouping.
"""
from __future__ import annotations

import math
import uuid
from typing import Any, Optional

from langchain_core.tools import tool

from nova.agents.level3.supplier_tool import find_supplier


@tool
def create_purchase_order(
    material_code: str,
    material_name: str,
    quantity: float,
    unit: str,
    priority: str = "NORMAL",
    supplier_id: str = "",
    unit_price: Optional[float] = None,
) -> dict[str, Any]:
    """Create a single purchase order for a required material with deficit buffer."""
    order_id = f"PO-{uuid.uuid4().hex[:8].upper()}"

    # Calculate 10% safety reserve buffer
    buffered_qty = round(quantity * 1.10, 2)

    # Resolve supplier if not provided
    supplier_info = None
    if supplier_id:
        supplier_info = {"supplier_id": supplier_id}
    else:
        supplier_info = find_supplier.invoke({"material_name": material_name})

    price = unit_price or supplier_info.get("unit_price_kzt") or 0.0
    total_amount = round(buffered_qty * price, 2)

    return {
        "order_id": order_id,
        "item_code": material_code,
        "name": material_name,
        "raw_quantity": quantity,
        "quantity": buffered_qty,
        "safety_buffer_pct": 10.0,
        "unit": unit,
        "unit_price_kzt": price,
        "total_amount_kzt": total_amount,
        "priority": priority.upper(),
        "supplier_id": supplier_info.get("supplier_id"),
        "supplier_name": supplier_info.get("supplier_name"),
        "delivery_days": supplier_info.get("delivery_days", 3),
        "status": "DRAFT",
    }


def build_purchase_orders_from_stock_check(
    stock_check_items: dict[str, Any],
    target_city: str = "Алматы",
) -> list[dict[str, Any]]:
    """Convert batch stock check deficit items into grouped purchase orders."""
    orders: list[dict[str, Any]] = []
    order_counter = 1

    for key, item in stock_check_items.items():
        deficit = float(item.get("deficit", 0.0))
        if deficit <= 0.001:
            continue

        code = item.get("code", "")
        name = item.get("name", "")
        unit = item.get("unit", "ед")
        required = float(item.get("required", 0.0))

        # Deficit > 80% of requirement -> URGENT priority
        is_urgent = (deficit / required >= 0.8) if required > 0 else False
        priority = "URGENT" if is_urgent else "NORMAL"

        # Apply +10% safety buffer
        buffered_qty = round(deficit * 1.10, 2)

        # Lookup supplier
        supplier = find_supplier.invoke({
            "material_name": name,
            "category": item.get("category", ""),
            "city": target_city,
        })

        unit_price = (
            supplier.get("unit_price_kzt")
            or item.get("unit_price")
            or 0.0
        )
        total_kzt = round(buffered_qty * unit_price, 2)

        orders.append({
            "order_id": f"PO-2026-{order_counter:03d}",
            "item_code": code,
            "name": name,
            "required_quantity": required,
            "in_stock_quantity": item.get("available", 0.0),
            "deficit_quantity": deficit,
            "order_quantity": buffered_qty,
            "safety_buffer_pct": 10.0,
            "unit": unit,
            "unit_price_kzt": unit_price,
            "total_amount_kzt": total_kzt,
            "priority": priority,
            "supplier_id": supplier.get("supplier_id"),
            "supplier_name": supplier.get("supplier_name"),
            "supplier_phone": supplier.get("phone"),
            "delivery_days": supplier.get("delivery_days", 2),
            "status": "APPROVED_FOR_PURCHASE",
        })
        order_counter += 1

    return orders


__all__ = [
    "create_purchase_order",
    "build_purchase_orders_from_stock_check",
]
