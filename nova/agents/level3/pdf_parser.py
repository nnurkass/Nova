"""Document parser contracts for PDF/DOCX tender attachments."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from PyPDF2 import PdfReader


SECTION_KEYS = (
    "technical_specification",
    "requirements",
    "work_scope",
)

SECTION_HEADINGS: dict[str, tuple[str, ...]] = {
    "technical_specification": (
        "technical specification",
        "technical assignment",
        "техническое задание",
        "техническая спецификация",
        "тех задание",
        "тз",
    ),
    "requirements": (
        "requirements",
        "qualification requirements",
        "требования",
        "квалификационные требования",
    ),
    "work_scope": (
        "work scope",
        "scope of work",
        "volumes of work",
        "объемы работ",
        "перечень работ",
    ),
}


class DocumentParseError(ValueError):
    """Raised when a document cannot be parsed into a structured payload."""


def _normalize_text(text: str) -> str:
    """Normalize spacing while preserving paragraph boundaries."""
    lines = [" ".join(line.strip().split()) for line in text.replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line)


def _empty_sections() -> dict[str, str]:
    return {key: "" for key in SECTION_KEYS}


def _normalize_heading(value: str) -> str:
    lowered = value.lower().replace("ё", "е")
    cleaned = re.sub(r"[^a-zа-я0-9 ]+", " ", lowered, flags=re.IGNORECASE)
    return " ".join(cleaned.split())


def _detect_section_heading(line: str) -> str | None:
    normalized = _normalize_heading(line)
    if not normalized:
        return None

    for key, aliases in SECTION_HEADINGS.items():
        for alias in aliases:
            if normalized == alias:
                return key
            if normalized.startswith(f"{alias} ") and len(normalized) <= len(alias) + 4:
                return key
    return None


def _split_sections(text: str) -> dict[str, str]:
    """Best-effort section splitter based on heading aliases."""

    normalized = _normalize_text(text)
    sections = _empty_sections()
    if not normalized:
        return sections

    active_key = "technical_specification"
    bucket: dict[str, list[str]] = {key: [] for key in SECTION_KEYS}

    for line in normalized.splitlines():
        heading_key = _detect_section_heading(line)
        if heading_key is not None:
            active_key = heading_key
            continue
        bucket[active_key].append(line)

    for key in SECTION_KEYS:
        sections[key] = "\n".join(bucket[key]).strip()

    if not any(sections.values()):
        sections["technical_specification"] = normalized

    return sections


def _normalize_table_rows(rows: list[list[str]]) -> dict[str, list[list[str]] | list[str]]:
    if not rows:
        return {"headers": [], "rows": []}

    width = max(len(row) for row in rows)
    normalized_rows: list[list[str]] = []
    for row in rows:
        normalized = row + [""] * (width - len(row))
        if any(cell.strip() for cell in normalized):
            normalized_rows.append([_normalize_text(cell) for cell in normalized])

    if not normalized_rows:
        return {"headers": [], "rows": []}

    return {
        "headers": normalized_rows[0],
        "rows": normalized_rows[1:],
    }


def _extract_docx_with_python_docx(path: Path) -> tuple[list[str], list[dict[str, list[list[str]] | list[str]]]]:
    from docx import Document  # type: ignore[import-not-found]

    document = Document(str(path))
    paragraphs = [_normalize_text(paragraph.text) for paragraph in document.paragraphs if paragraph.text.strip()]
    tables: list[dict[str, list[list[str]] | list[str]]] = []

    for table in document.tables:
        rows = []
        for row in table.rows:
            cells = [_normalize_text(cell.text) for cell in row.cells]
            if any(cells):
                rows.append(cells)
        normalized = _normalize_table_rows(rows)
        if normalized["headers"]:
            tables.append(normalized)

    return paragraphs, tables


def _extract_docx_with_xml(path: Path) -> tuple[list[str], list[dict[str, list[list[str]] | list[str]]]]:
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    try:
        with zipfile.ZipFile(path, "r") as archive:
            document_xml = archive.read("word/document.xml")
    except Exception as exc:  # pragma: no cover - defensive path
        raise DocumentParseError(f"Failed to read DOCX zip container: {path}") from exc

    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError as exc:  # pragma: no cover - defensive path
        raise DocumentParseError(f"Invalid DOCX XML payload: {path}") from exc

    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:body/w:p", ns):
        fragments = [node.text or "" for node in paragraph.findall(".//w:t", ns)]
        text = _normalize_text(" ".join(fragments))
        if text:
            paragraphs.append(text)

    tables: list[dict[str, list[list[str]] | list[str]]] = []
    for table in root.findall(".//w:body/w:tbl", ns):
        rows: list[list[str]] = []
        for row in table.findall("./w:tr", ns):
            cells: list[str] = []
            for cell in row.findall("./w:tc", ns):
                fragments = [node.text or "" for node in cell.findall(".//w:t", ns)]
                cells.append(_normalize_text(" ".join(fragments)))
            if any(cells):
                rows.append(cells)
        normalized = _normalize_table_rows(rows)
        if normalized["headers"]:
            tables.append(normalized)

    return paragraphs, tables


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
    try:
        reader = PdfReader(str(path))
        text_chunks = [page.extract_text() or "" for page in reader.pages]
        text = _normalize_text("\n".join(text_chunks))
    except Exception as exc:  # pragma: no cover - defensive, triggered in broken-file test
        raise DocumentParseError(f"Failed to parse PDF file: {path}") from exc

    if not text:
        raise DocumentParseError(f"No extractable text found in PDF: {path}")

    return {
        "document_type": "pdf",
        "file_path": str(path),
        "text": text,
        "sections": _split_sections(text),
        "tables": [],
        "metadata": {
            "page_count": len(reader.pages),
        },
    }


def parse_docx(file_path: str | Path) -> dict[str, Any]:
    """Parse DOCX content into a unified intermediate document structure."""

    path = _validate_path(file_path, expected_suffix=".docx")
    parser_backend = "python-docx"
    try:
        paragraphs, tables = _extract_docx_with_python_docx(path)
    except Exception:
        parser_backend = "xml-fallback"
        paragraphs, tables = _extract_docx_with_xml(path)

    text = _normalize_text("\n".join(paragraphs))
    if not text and not tables:
        raise DocumentParseError(f"No extractable content found in DOCX: {path}")

    return {
        "document_type": "docx",
        "file_path": str(path),
        "text": text,
        "sections": _split_sections(text),
        "tables": tables,
        "metadata": {
            "paragraph_count": len(paragraphs),
            "table_count": len(tables),
            "parser_backend": parser_backend,
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
