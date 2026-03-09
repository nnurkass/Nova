"""Unit tests for the ABC PDF/JSON adapter."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

from nova.config import reset_settings_cache
from nova.integrations.abc import read_abc_document, read_abc_xml, write_abc_xml
from nova.integrations.abc.models import EstimatePosition
from nova.integrations.abc.writer import serialize_abc_statement, write_abc_statement


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "abc_pdf"
SAMPLE_PDF = FIXTURE_DIR / "sample_statement.pdf"
NO_SECTIONS_PDF = FIXTURE_DIR / "no_sections.pdf"


class TestABCReader:
    def test_read_abc_document_parses_q9_qm_and_id(self):
        statement = read_abc_document(SAMPLE_PDF)

        assert statement.meta is not None
        assert statement.meta.source_format == "abc_pdf"
        assert statement.meta.project_name == "Training pool project"
        assert statement.meta.construction_cipher == "25-04"
        assert statement.meta.estimate_code == "02-01-01"
        assert statement.meta.page_ranges == {"Q9": [1], "QM": [2], "ID": [3]}

        assert [work.name for work in statement.works] == [
            "Roofing-dismantling",
            "Cable-dismantling",
        ]
        assert [material.name for material in statement.materials] == [
            "Technical-acetylene",
            "Electrode-E42",
        ]
        assert [position.section_name for position in statement.positions] == [
            "Q9",
            "Q9",
            "QM",
            "QM",
        ]
        assert statement.total_works_cost == 58000.0
        assert statement.total_materials_cost == 3478377.2

    def test_read_abc_xml_is_compatibility_alias(self):
        canonical = read_abc_document(SAMPLE_PDF)
        compatibility = read_abc_xml(SAMPLE_PDF)

        assert compatibility.model_dump(mode="json") == canonical.model_dump(mode="json")

    def test_read_abc_document_raises_for_missing_file(self):
        with pytest.raises(FileNotFoundError):
            read_abc_document(FIXTURE_DIR / "missing.pdf")

    def test_read_abc_document_raises_for_unrecognized_pdf(self):
        with pytest.raises(ValueError, match="does not contain Q9/QM/ID sections"):
            read_abc_document(NO_SECTIONS_PDF)


class TestABCModelsAndWriter:
    def test_estimate_position_syncs_type_from_compatibility_flag(self):
        position = EstimatePosition(
            position_number=1,
            code="MAT-1",
            name="Synthetic material",
            unit="kg",
            quantity=5,
            is_work=False,
        )

        assert position.position_type == "material"
        assert position.is_work is False

    def test_write_abc_statement_emits_stable_json(self, tmp_path: Path):
        statement = read_abc_document(SAMPLE_PDF)
        output_path = tmp_path / "statement.json"

        first = write_abc_statement(statement, output_path)
        first_text = first.read_text(encoding="utf-8")
        second = write_abc_xml(statement, output_path)
        second_text = second.read_text(encoding="utf-8")

        assert first == output_path
        assert second == output_path
        assert first_text == second_text
        assert json.loads(first_text) == serialize_abc_statement(statement)


class TestABCTools:
    def test_abc_tool_module_import_is_safe_without_eager_settings_resolution(self):
        sys.modules.pop("nova.agents.level3.abc_tool", None)
        module = importlib.import_module("nova.agents.level3.abc_tool")

        assert module.abc_document_reader.name == "abc_document_reader"

    def test_tool_wrappers_support_relative_paths(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        monkeypatch.setenv("ABC_EXPORT_PATH", str(FIXTURE_DIR))
        monkeypatch.setenv("ABC_IMPORT_PATH", str(tmp_path))
        reset_settings_cache()

        from nova.agents.level3.abc_tool import (
            abc_document_reader,
            abc_statement_writer,
            abc_xml_reader,
            abc_xml_writer,
        )

        payload = abc_document_reader.invoke({"file_path": "sample_statement.pdf"})
        compatibility_payload = abc_xml_reader.invoke({"file_path": "sample_statement.pdf"})
        result = abc_statement_writer.invoke(
            {"data": payload, "output_path": "statement.json"}
        )
        compatibility_result = abc_xml_writer.invoke(
            {"data": payload, "output_path": "statement_alias.json"}
        )

        assert payload["source_path"] == str(SAMPLE_PDF)
        assert compatibility_payload["works"] == payload["works"]
        assert Path(result["output_path"]).exists()
        assert Path(compatibility_result["output_path"]).exists()
        assert result["positions"] == 4
        assert compatibility_result["materials"] == 2

        reset_settings_cache()
