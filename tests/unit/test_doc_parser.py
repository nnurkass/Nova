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


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_single_page_pdf(lines: list[str]) -> bytes:
    text_ops = ["BT", "/F1 12 Tf", "72 760 Td"]
    for index, line in enumerate(lines):
        if index:
            text_ops.append("0 -16 Td")
        text_ops.append(f"({_escape_pdf_text(line)}) Tj")
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode("latin-1")

    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n",
        (
            b"3 0 obj\n"
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> "
            b"/Contents 5 0 R >>\n"
            b"endobj\n"
        ),
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        (
            b"5 0 obj\n"
            + f"<< /Length {len(stream)} >>\n".encode("ascii")
            + b"stream\n"
            + stream
            + b"\nendstream\nendobj\n"
        ),
    ]

    parts: list[bytes] = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for obj in objects:
        offsets.append(sum(len(part) for part in parts))
        parts.append(obj)

    xref_offset = sum(len(part) for part in parts)
    xref_lines = ["xref", "0 6", "0000000000 65535 f "]
    xref_lines.extend(f"{offset:010d} 00000 n " for offset in offsets[1:])
    xref = "\n".join(xref_lines).encode("ascii") + b"\n"
    trailer = (
        b"trailer\n"
        b"<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )
    return b"".join(parts) + xref + trailer


def test_parse_pdf_contract_returns_expected_keys(tmp_path: Path):
    sample = tmp_path / "sample.pdf"
    sample.write_bytes(
        _build_single_page_pdf(
            [
                "Technical specification",
                "Build school foundation and walls",
                "Requirements",
                "Use certified personnel and PPE",
                "Work scope",
                "Earth works 120 m3",
            ]
        )
    )

    payload = parse_pdf(sample)

    assert payload["document_type"] == "pdf"
    assert "Build school foundation and walls" in payload["text"]
    assert set(payload["sections"]) == {"technical_specification", "requirements", "work_scope"}
    assert payload["sections"]["requirements"] == "Use certified personnel and PPE"
    assert payload["sections"]["work_scope"] == "Earth works 120 m3"
    assert payload["tables"] == []
    assert payload["metadata"]["page_count"] == 1


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
