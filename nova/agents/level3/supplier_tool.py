"""
LangChain tool for supplier search and pricing in Kazakhstan.

Queries suppliers database (data/suppliers_mock.json) to find matching
vendors, delivery conditions, and market prices.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
SUPPLIERS_FILE = DATA_DIR / "suppliers_mock.json"


def load_suppliers_data() -> list[dict[str, Any]]:
    """Load suppliers directory from JSON file."""
    if not SUPPLIERS_FILE.exists():
        logger.warning("Suppliers file not found: %s", SUPPLIERS_FILE)
        return []
    try:
        with open(SUPPLIERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load suppliers: %s", exc)
        return []


@tool
def find_supplier(
    material_name: str = "",
    category: str = "",
    city: str = "",
) -> dict[str, Any]:
    """Find the best supplier for a given material name, category, or delivery city."""
    suppliers = load_suppliers_data()
    mat_clean = material_name.strip().lower()
    cat_clean = category.strip().lower()
    city_clean = city.strip().lower()

    candidates: list[dict[str, Any]] = []

    for sup in suppliers:
        # Check if supplier has exact item
        item_match = None
        for item in sup.get("items", []):
            if mat_clean and (mat_clean in item.get("name", "").lower() or item.get("name", "").lower() in mat_clean):
                item_match = item
                break

        # Check category match
        cat_match = any(cat_clean in c.lower() for c in sup.get("categories", [])) if cat_clean else False

        # Check city match
        city_match = city_clean in sup.get("city", "").lower() if city_clean else True

        score = 0
        if item_match:
            score += 10
        if cat_match:
            score += 5
        if city_match:
            score += 3
        score += float(sup.get("rating", 4.0))

        if item_match or cat_match or not (mat_clean or cat_clean):
            candidates.append({
                "supplier": sup,
                "matched_item": item_match,
                "score": score,
            })

    if not candidates and suppliers:
        candidates.append({"supplier": suppliers[0], "matched_item": None, "score": 1})

    candidates.sort(key=lambda x: x["score"], reverse=True)
    best = candidates[0]
    sup_info = best["supplier"]
    matched_item = best["matched_item"]

    return {
        "found": True,
        "supplier_id": sup_info.get("id"),
        "supplier_name": sup_info.get("name"),
        "bin": sup_info.get("bin"),
        "city": sup_info.get("city"),
        "phone": sup_info.get("phone"),
        "email": sup_info.get("email"),
        "rating": sup_info.get("rating"),
        "delivery_days": sup_info.get("delivery_days"),
        "unit_price_kzt": matched_item.get("price_kzt") if matched_item else None,
        "item_name": matched_item.get("name") if matched_item else material_name,
    }


def list_suppliers(category: str = "") -> list[dict[str, Any]]:
    """List all available suppliers, optionally filtered by category."""
    suppliers = load_suppliers_data()
    if not category:
        return suppliers
    cat_clean = category.strip().lower()
    return [
        s for s in suppliers
        if any(cat_clean in c.lower() for c in s.get("categories", []))
    ]


__all__ = [
    "find_supplier",
    "list_suppliers",
    "load_suppliers_data",
]
