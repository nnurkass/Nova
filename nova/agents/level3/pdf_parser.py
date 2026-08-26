"""
Document parsing tools for tender technical specifications and estimates.

Extracts text content, work schedules, and materials lists from PDF and
structured estimate documents with ABC adapter integration.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from PyPDF2 import PdfReader

from nova.integrations.abc.reader import read_abc_document

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str | Path) -> dict[str, Any]:
    """Extract full text and metadata from a PDF file."""
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {path}", "pages_count": 0, "text": ""}

    try:
        reader = PdfReader(str(path))
        pages_text: list[str] = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_text.append(text)

        full_text = "\n".join(pages_text)
        return {
            "file_name": path.name,
            "pages_count": len(reader.pages),
            "pages_text": pages_text,
            "text": full_text,
        }
    except Exception as exc:
        logger.error("Failed to parse PDF %s: %s", path, exc)
        return {"error": str(exc), "pages_count": 0, "text": ""}


@tool
def extract_work_list(file_path: str) -> list[dict[str, Any]]:
    """Extract structured list of construction works (BOQ) from technical documentation."""
    path = Path(file_path)
    if not path.exists():
        return []

    # First attempt: Try reading as ABC document
    try:
        statement = read_abc_document(path)
        if statement.works:
            return [w.model_dump() for w in statement.works]
    except Exception:
        pass

    # Second attempt: Heuristic PDF text parsing
    parsed = parse_pdf(path)
    text = parsed.get("text", "")
    works: list[dict[str, Any]] = []

    # Regex patterns for line items: e.g. "1.1 Демонтаж кровли м2 500"
    work_pattern = re.compile(
        r"(?:(?:[0-9]+[\.\-\_][0-9]+)|(?:ВОР\-[0-9]+))\s+([^\n\d]+)\s+([а-яА-Яa-zA-Z0-9\/\^]{1,6})\s+([0-9]+(?:[\.\,][0-9]+)?)"
    )

    for match in work_pattern.finditer(text):
        name = match.group(1).strip()
        unit = match.group(2).strip()
        qty_str = match.group(3).replace(",", ".")
        try:
            qty = float(qty_str)
            code = f"W-{len(works)+1:02d}"
            works.append({
                "code": code,
                "name": name,
                "unit": unit,
                "quantity": qty,
                "price": None,
            })
        except ValueError:
            continue

    return works


@tool
def extract_materials(file_path: str) -> list[dict[str, Any]]:
    """Extract structured bill of materials from tender estimate documentation."""
    path = Path(file_path)
    if not path.exists():
        return []

    # First attempt: ABC statement
    try:
        statement = read_abc_document(path)
        if statement.materials:
            return [m.model_dump() for m in statement.materials]
    except Exception:
        pass

    # Second attempt: PDF parsing
    parsed = parse_pdf(path)
    text = parsed.get("text", "")
    materials: list[dict[str, Any]] = []

    mat_pattern = re.compile(
        r"(?:([0-9]{3}\-[0-9]{4}|МАТ\-[0-9]+))\s+([^\n\d]+)\s+([а-яА-Яa-zA-Z0-9\/\^]{1,6})\s+([0-9]+(?:[\.\,][0-9]+)?)"
    )

    for match in mat_pattern.finditer(text):
        code = match.group(1).strip()
        name = match.group(2).strip()
        unit = match.group(3).strip()
        qty_str = match.group(4).replace(",", ".")
        try:
            qty = float(qty_str)
            materials.append({
                "code": code,
                "name": name,
                "unit": unit,
                "quantity": qty,
                "price": None,
            })
        except ValueError:
            continue

    return materials


__all__ = [
    "parse_pdf",
    "extract_work_list",
    "extract_materials",
]
