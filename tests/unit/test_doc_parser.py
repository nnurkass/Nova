"""Unit tests for document parser contracts."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import pytest

from nova.agents.level3.pdf_parser import (
    DocumentParseError,
    extract_materials,
    extract_work_list,
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


def _build_docx(paragraphs: list[str], table_rows: list[list[str]] | None = None) -> bytes:
    paragraph_xml = "".join(
        f"<w:p><w:r><w:t>{xml_escape(paragraph)}</w:t></w:r></w:p>"
        for paragraph in paragraphs
    )

    table_xml = ""
    if table_rows:
        rows = []
        for row in table_rows:
            cells = "".join(
                f"<w:tc><w:p><w:r><w:t>{xml_escape(cell)}</w:t></w:r></w:p></w:tc>"
                for cell in row
            )
            rows.append(f"<w:tr>{cells}</w:tr>")
        table_xml = f"<w:tbl>{''.join(rows)}</w:tbl>"

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{paragraph_xml}{table_xml}<w:sectPr/></w:body>"
        "</w:document>"
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    document_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", rels_xml)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/_rels/document.xml.rels", document_rels_xml)
    return buffer.getvalue()


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
    sample.write_bytes(
        _build_docx(
            paragraphs=[
                "Technical specification",
                "Construction of school gym block",
                "Requirements",
                "Use certified concrete grade M350",
            ],
            table_rows=[
                ["Code", "Name", "Unit", "Qty"],
                ["W-01", "Earth works", "m3", "120"],
                ["W-02", "Concrete pouring", "m3", "45"],
            ],
        )
    )

    payload = parse_docx(sample)

    assert payload["document_type"] == "docx"
    assert "Construction of school gym block" in payload["text"]
    assert set(payload["sections"]) == {"technical_specification", "requirements", "work_scope"}
    assert payload["sections"]["requirements"] == "Use certified concrete grade M350"
    assert len(payload["tables"]) == 1
    assert payload["tables"][0]["headers"] == ["Code", "Name", "Unit", "Qty"]
    assert payload["tables"][0]["rows"][0] == ["W-01", "Earth works", "m3", "120"]
    assert payload["metadata"]["table_count"] == 1


def test_parse_document_unsupported_extension_raises(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("not supported", encoding="utf-8")

    with pytest.raises(DocumentParseError, match="Unsupported document type"):
        parse_document(sample)


def test_extract_work_list_from_docx_table(tmp_path: Path):
    sample = tmp_path / "work_scope.docx"
    sample.write_bytes(
        _build_docx(
            paragraphs=[
                "Technical specification",
                "General civil works package for school extension.",
            ],
            table_rows=[
                ["Code", "Name", "Unit", "Qty"],
                ["W-01", "Earth works", "m3", "120"],
                ["W-02", "Concrete pouring", "m3", "45"],
                ["M-01", "Cement", "t", "25"],
            ],
        )
    )

    result = extract_work_list.invoke({"file_path": str(sample)})
    payload = json.loads(result)

    assert payload["tool"] == "extract_work_list"
    assert payload["status"] == "ok"
    assert payload["counts"]["work_items"] == 2
    assert [item["code"] for item in payload["work_list"]] == ["W-01", "W-02"]
    assert payload["source_sections"] == ["tables"]


def test_extract_work_list_from_pdf_text_section(tmp_path: Path):
    sample = tmp_path / "work_scope.pdf"
    sample.write_bytes(
        _build_single_page_pdf(
            [
                "Technical specification",
                "General project description",
                "Work scope",
                "Earth works 120 m3",
                "Concrete pouring 45 m3",
            ]
        )
    )

    result = extract_work_list.invoke({"file_path": str(sample)})
    payload = json.loads(result)

    assert payload["status"] == "ok"
    assert payload["counts"]["work_items"] == 2
    assert payload["source_sections"] == ["work_scope"]


def test_extract_materials_from_docx_table(tmp_path: Path):
    sample = tmp_path / "materials.docx"
    sample.write_bytes(
        _build_docx(
            paragraphs=[
                "Technical specification",
                "Materials should follow project catalog.",
                "Requirements",
                "Cement M400 25 t",
            ],
            table_rows=[
                ["Code", "Material name", "Unit", "Qty"],
                ["M-01", "Cement M400", "t", "25"],
                ["M-02", "Rebar A500", "kg", "1400"],
                ["W-99", "Concrete pouring", "m3", "45"],
            ],
        )
    )

    result = extract_materials.invoke({"file_path": str(sample)})
    payload = json.loads(result)

    assert payload["tool"] == "extract_materials"
    assert payload["status"] == "ok"
    assert payload["counts"]["material_items"] == 2
    assert [item["code"] for item in payload["materials_list"]] == ["M-01", "M-02"]
    assert payload["source_sections"] == ["requirements", "tables"]


def test_level3_exports_document_tools():
    from nova.agents.level3 import (
        MaterialExtractionToolInput,
        WorkExtractionToolInput,
        extract_materials as exported_extract_materials,
        extract_work_list as exported_extract_work_list,
        parse_docx as exported_parse_docx,
        parse_pdf as exported_parse_pdf,
    )

    assert exported_extract_work_list.name == "extract_work_list"
    assert exported_extract_materials.name == "extract_materials"
    assert WorkExtractionToolInput.model_fields["file_path"].annotation is str
    assert MaterialExtractionToolInput.model_fields["file_path"].annotation is str
    assert callable(exported_parse_pdf)
    assert callable(exported_parse_docx)
