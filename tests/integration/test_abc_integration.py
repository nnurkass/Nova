"""Integration tests for the ABC PDF/JSON adapter."""
from __future__ import annotations

import json
from pathlib import Path

from nova.integrations.abc import read_abc_document, write_abc_statement
from nova.integrations.abc.writer import deserialize_abc_statement


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "abc_pdf"
SAMPLE_PDF = FIXTURE_DIR / "sample_statement.pdf"
SNAPSHOT_JSON = FIXTURE_DIR / "expected_statement.json"


def test_abc_pdf_roundtrip_matches_snapshot(tmp_path: Path):
    statement = read_abc_document(SAMPLE_PDF)
    output_path = tmp_path / "roundtrip.json"

    written = write_abc_statement(statement, output_path)
    payload = json.loads(written.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT_JSON.read_text(encoding="utf-8"))
    restored = deserialize_abc_statement(payload)

    assert payload == snapshot
    assert restored.meta is not None
    assert restored.meta.page_ranges == {"Q9": [1], "QM": [2], "ID": [3]}
    assert [work.code for work in restored.works] == [
        "6111-0402-0202",
        "1217-0101-0601",
    ]
    assert [material.code for material in restored.materials] == [
        "217-605-0108",
        "217-301-0105",
    ]
