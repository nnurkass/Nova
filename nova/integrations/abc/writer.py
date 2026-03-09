"""
JSON writer for normalized ABC resource statements.

This is a transitional compatibility layer for Step 2.4. XML-specific aliases
are preserved until a real XML adapter is implemented.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nova.integrations.abc.models import (
    ABCMaterial,
    ABCWork,
    EstimateDocumentMeta,
    EstimatePosition,
    ResourceStatement,
)


def _compact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: compacted
            for key, item in value.items()
            if (compacted := _compact(item)) is not None
        }
    if isinstance(value, list):
        return [compacted for item in value if (compacted := _compact(item)) is not None]
    if value is None:
        return None
    return value


def serialize_abc_statement(statement: ResourceStatement) -> dict[str, Any]:
    """Return a stable JSON-serializable payload for a resource statement."""
    payload = {
        "meta": statement.meta.model_dump(mode="json") if statement.meta else None,
        "positions": [position.model_dump(mode="json") for position in statement.positions],
        "works": [work.model_dump(mode="json") for work in statement.works],
        "materials": [material.model_dump(mode="json") for material in statement.materials],
        "totals": {
            "works": statement.total_works_cost,
            "materials": statement.total_materials_cost,
        },
    }
    return _compact(payload)


def deserialize_abc_statement(payload: dict[str, Any]) -> ResourceStatement:
    """Hydrate a resource statement from the normalized JSON payload shape."""
    totals = payload.get("totals", {}) or {}
    return ResourceStatement(
        meta=EstimateDocumentMeta.model_validate(payload["meta"]) if payload.get("meta") else None,
        positions=[
            EstimatePosition.model_validate(position)
            for position in payload.get("positions", [])
        ],
        works=[ABCWork.model_validate(work) for work in payload.get("works", [])],
        materials=[
            ABCMaterial.model_validate(material)
            for material in payload.get("materials", [])
        ],
        total_works_cost=totals.get("works"),
        total_materials_cost=totals.get("materials"),
    )


def write_abc_statement(statement: ResourceStatement, output_path: str | Path) -> Path:
    """Write a normalized ABC statement as stable UTF-8 JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = serialize_abc_statement(statement)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    return path


def write_abc_xml(statement: ResourceStatement, output_path: str | Path) -> Path:
    """Compatibility alias preserved until a real XML adapter is implemented."""
    return write_abc_statement(statement, output_path)


__all__ = [
    "deserialize_abc_statement",
    "serialize_abc_statement",
    "write_abc_statement",
    "write_abc_xml",
]
