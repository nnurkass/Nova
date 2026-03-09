"""
LangChain tools for the ABC PDF/JSON adapter.

Canonical tools expose PDF reading and JSON statement writing. XML-specific
names are temporary compatibility aliases only.

Implemented in Step 2.4.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from nova.config import get_settings
from nova.integrations.abc.reader import read_abc_document
from nova.integrations.abc.writer import (
    deserialize_abc_statement,
    serialize_abc_statement,
    write_abc_statement,
)


def _resolve_input_path(file_path: str | Path) -> Path:
    settings = get_settings()
    path = Path(file_path)
    if path.is_absolute():
        return path
    return Path(settings.abc_export_path) / path


def _resolve_output_path(output_path: str | Path) -> Path:
    settings = get_settings()
    path = Path(output_path)
    if path.is_absolute():
        return path
    return Path(settings.abc_import_path) / path


@tool
def abc_document_reader(file_path: str) -> dict[str, Any]:
    """Read an ABC-generated PDF and return a normalized statement payload."""
    resolved_path = _resolve_input_path(file_path)
    statement = read_abc_document(resolved_path)
    payload = serialize_abc_statement(statement)
    payload["source_path"] = str(resolved_path)
    return payload


@tool
def abc_statement_writer(data: dict[str, Any], output_path: str) -> dict[str, Any]:
    """Write a normalized ABC statement payload to a JSON file."""
    statement = deserialize_abc_statement(data)
    resolved_path = _resolve_output_path(output_path)
    written_path = write_abc_statement(statement, resolved_path)
    return {
        "output_path": str(written_path),
        "format": "json",
        "positions": len(statement.positions),
        "works": len(statement.works),
        "materials": len(statement.materials),
    }


@tool
def abc_xml_reader(file_path: str) -> dict[str, Any]:
    """Compatibility alias for abc_document_reader until XML support is added."""
    return abc_document_reader.invoke({"file_path": file_path})


@tool
def abc_xml_writer(data: dict[str, Any], output_path: str) -> dict[str, Any]:
    """Compatibility alias for abc_statement_writer until XML support is added."""
    return abc_statement_writer.invoke({"data": data, "output_path": output_path})


__all__ = [
    "abc_document_reader",
    "abc_statement_writer",
    "abc_xml_reader",
    "abc_xml_writer",
]
