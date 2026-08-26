"""Unit tests for data fixtures integrity and structure."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class TestFixtures:
    def test_sample_tenders_fixture_valid(self):
        tenders_path = DATA_DIR / "sample_tenders.json"
        assert tenders_path.exists(), "sample_tenders.json must exist"

        with open(tenders_path, "r", encoding="utf-8") as f:
            tenders = json.load(f)

        assert isinstance(tenders, list)
        assert len(tenders) >= 3, "Should contain at least 3 realistic tenders"

        for item in tenders:
            assert "id" in item
            assert "name_ru" in item
            assert "total_sum" in item
            assert float(item["total_sum"]) > 0
            assert "lots" in item
            assert len(item["lots"]) >= 1

    def test_warehouse_fixture_valid(self):
        warehouse_path = DATA_DIR / "warehouse_mock.json"
        assert warehouse_path.exists(), "warehouse_mock.json must exist"

        with open(warehouse_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        assert isinstance(items, list)
        assert len(items) >= 30, "Warehouse should have 30+ items"

        for item in items:
            assert "code" in item
            assert "name" in item
            assert "in_stock" in item
            assert "unit" in item
            assert "price_kzt" in item
            assert float(item["price_kzt"]) >= 0

    def test_suppliers_fixture_valid(self):
        suppliers_path = DATA_DIR / "suppliers_mock.json"
        assert suppliers_path.exists(), "suppliers_mock.json must exist"

        with open(suppliers_path, "r", encoding="utf-8") as f:
            suppliers = json.load(f)

        assert isinstance(suppliers, list)
        assert len(suppliers) >= 5, "Should have at least 5 suppliers"

        for sup in suppliers:
            assert "id" in sup
            assert "name" in sup
            assert "bin" in sup
            assert "categories" in sup
            assert "items" in sup
            assert len(sup["items"]) >= 1
