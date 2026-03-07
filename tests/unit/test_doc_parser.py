"""Unit tests for document parser contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from nova.agents.level3.pdf_parser import (
    DocumentParseError,
    parse_docx,
    parse_document,
    parse_pdf,
)


def test_parse_pdf_contract_returns_expected_keys(tmp_path: Path):
    sample = tmp_path / "sample.pdf"
    sample.write_bytes(b"%PDF-1.4\n")

    payload = parse_pdf(sample)

    assert payload["document_type"] == "pdf"
    assert payload["text"] == ""
    assert set(payload["sections"]) == {"technical_specification", "requirements", "work_scope"}
    assert payload["tables"] == []


def test_parse_docx_contract_returns_expected_keys(tmp_path: Path):
    sample = tmp_path / "sample.docx"
    sample.write_bytes(b"PK\x03\x04")

    payload = parse_docx(sample)

    assert payload["document_type"] == "docx"
    assert payload["text"] == ""
    assert set(payload["sections"]) == {"technical_specification", "requirements", "work_scope"}
    assert payload["tables"] == []


def test_parse_document_unsupported_extension_raises(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("not supported", encoding="utf-8")

    with pytest.raises(DocumentParseError, match="Unsupported document type"):
        parse_document(sample)
