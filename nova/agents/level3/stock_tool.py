"""
LangChain tool for warehouse stock verification.

Queries warehouse mock database (data/warehouse_mock.json) to check
available quantities, reserved items, locations, and unit costs.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
WAREHOUSE_FILE = DATA_DIR / "warehouse_mock.json"


def load_warehouse_data() -> list[dict[str, Any]]:
    """Load warehouse stock items from JSON file."""
    if not WAREHOUSE_FILE.exists():
        logger.warning("Warehouse file not found: %s", WAREHOUSE_FILE)
        return []
    try:
        with open(WAREHOUSE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load warehouse items: %s", exc)
        return []


def find_stock_item(material_code: str = "", material_name: str = "") -> Optional[dict[str, Any]]:
    """Find a warehouse item by code or closest name match."""
    items = load_warehouse_data()
    code_clean = material_code.strip().lower()
    name_clean = material_name.strip().lower()

    # Exact code match
    if code_clean:
        for item in items:
            if item.get("code", "").strip().lower() == code_clean:
                return item

    # Exact or substring name match
    if name_clean:
        for item in items:
            item_name = item.get("name", "").strip().lower()
            if name_clean in item_name or item_name in name_clean:
                return item

        # Token match
        name_tokens = [t for t in name_clean.split() if len(t) > 2]
        for item in items:
            item_name = item.get("name", "").strip().lower()
            if any(t in item_name for t in name_tokens):
                return item

    return None


@tool
def check_stock(material_code: str = "", material_name: str = "") -> dict[str, Any]:
    """Check inventory stock level for a specific construction material by code or name."""
    item = find_stock_item(material_code, material_name)
    if not item:
        return {
            "found": False,
            "material_code": material_code,
            "material_name": material_name,
            "in_stock": 0.0,
            "reserved": 0.0,
            "available": 0.0,
            "unit": "ед",
            "price_kzt": 0.0,
            "message": "Позиция не найдена на складе",
        }

    in_stock = float(item.get("in_stock", 0.0))
    reserved = float(item.get("reserved", 0.0))
    available = max(0.0, in_stock - reserved)

    return {
        "found": True,
        "material_code": item.get("code"),
        "material_name": item.get("name"),
        "category": item.get("category"),
        "unit": item.get("unit"),
        "in_stock": in_stock,
        "reserved": reserved,
        "available": available,
        "price_kzt": float(item.get("price_kzt", 0.0)),
        "location": item.get("location"),
    }


def batch_check_stock(materials: list[dict[str, Any]]) -> dict[str, Any]:
    """Batch verify a list of required materials against warehouse stock."""
    results: dict[str, Any] = {}
    total_required_cost = 0.0
    total_in_stock_value = 0.0

    for mat in materials:
        code = mat.get("code", "")
        name = mat.get("name", "")
        qty = float(mat.get("quantity", 0.0))
        unit = mat.get("unit", "")
        stock = check_stock.invoke({"material_code": code, "material_name": name})

        available = stock["available"]
        unit_price = stock.get("price_kzt") or float(mat.get("price") or mat.get("estimated_price") or 0.0)
        deficit = max(0.0, qty - available)

        key = code or name
        results[key] = {
            "code": code,
            "name": name,
            "unit": unit or stock.get("unit", "ед"),
            "required": qty,
            "in_stock": stock["in_stock"],
            "reserved": stock["reserved"],
            "available": available,
            "deficit": deficit,
            "unit_price": unit_price,
            "covered_pct": round((available / qty * 100.0) if qty > 0 else 100.0, 1),
            "status": "IN_STOCK" if deficit == 0 else ("PARTIAL" if available > 0 else "DEFICIT"),
        }

        total_required_cost += qty * unit_price
        total_in_stock_value += min(qty, available) * unit_price

    return {
        "items": results,
        "summary": {
            "total_items": len(materials),
            "fully_in_stock": sum(1 for v in results.values() if v["status"] == "IN_STOCK"),
            "partial_stock": sum(1 for v in results.values() if v["status"] == "PARTIAL"),
            "full_deficit": sum(1 for v in results.values() if v["status"] == "DEFICIT"),
            "total_required_cost": round(total_required_cost, 2),
            "in_stock_covered_value": round(total_in_stock_value, 2),
            "to_purchase_estimated_cost": round(max(0.0, total_required_cost - total_in_stock_value), 2),
        },
    }


__all__ = [
    "check_stock",
    "batch_check_stock",
    "load_warehouse_data",
    "find_stock_item",
]
