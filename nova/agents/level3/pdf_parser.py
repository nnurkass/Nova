"""Document parser contracts for PDF/DOCX tender attachments."""

from __future__ import annotations

from pathlib import Path
from typing import Any


SECTION_KEYS = (
    "technical_specification",
    "requirements",
    "work_scope",
)


class DocumentParseError(ValueError):
    """Raised when a document cannot be parsed into a structured payload."""


def _normalize_text(text: str) -> str:
    """Normalize spacing while preserving paragraph boundaries."""
    lines = [" ".join(line.strip().split()) for line in text.replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line)


def _empty_sections() -> dict[str, str]:
    return {key: "" for key in SECTION_KEYS}


def _split_sections(text: str) -> dict[str, str]:
    """Best-effort section splitter placeholder.

    Full heading detection is implemented in later substeps.
    """

    normalized = _normalize_text(text)
    sections = _empty_sections()
    sections["technical_specification"] = normalized
    return sections


def _validate_path(file_path: str | Path, *, expected_suffix: str) -> Path:
    path = Path(file_path).expanduser()
    if not path.exists():
        raise DocumentParseError(f"File not found: {path}")
    if path.suffix.lower() != expected_suffix:
        raise DocumentParseError(
            f"Unsupported file extension for parser {expected_suffix}: {path.suffix.lower() or '<none>'}"
        )
    return path


def parse_pdf(file_path: str | Path) -> dict[str, Any]:
    """Parse PDF content into a unified intermediate document structure."""

    path = _validate_path(file_path, expected_suffix=".pdf")
    return {
        "document_type": "pdf",
        "file_path": str(path),
        "text": "",
        "sections": _empty_sections(),
        "tables": [],
        "metadata": {
            "page_count": 0,
        },
    }


def parse_docx(file_path: str | Path) -> dict[str, Any]:
    """Parse DOCX content into a unified intermediate document structure."""

    path = _validate_path(file_path, expected_suffix=".docx")
    return {
        "document_type": "docx",
        "file_path": str(path),
        "text": "",
        "sections": _empty_sections(),
        "tables": [],
        "metadata": {
            "paragraph_count": 0,
            "table_count": 0,
        },
    }


def parse_document(file_path: str | Path) -> dict[str, Any]:
    """Dispatch document parsing by file extension."""

    path = Path(file_path).expanduser()
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(path)
    if suffix == ".docx":
        return parse_docx(path)
    raise DocumentParseError(f"Unsupported document type: {suffix or '<none>'}")


__all__ = [
    "DocumentParseError",
    "SECTION_KEYS",
    "parse_docx",
    "parse_document",
    "parse_pdf",
]
