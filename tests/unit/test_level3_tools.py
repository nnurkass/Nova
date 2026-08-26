"""Unit tests for Level 3 LangChain tools."""
from pathlib import Path

from nova.agents.level3.goszakup_tool import (
    analyze_tender,
    download_tender_docs,
    goszakup_search,
    score_tender,
)
from nova.agents.level3.order_tool import (
    build_purchase_orders_from_stock_check,
    create_purchase_order,
)
from nova.agents.level3.pdf_parser import extract_materials, extract_work_list, parse_pdf
from nova.agents.level3.stock_tool import batch_check_stock, check_stock
from nova.agents.level3.supplier_tool import find_supplier, list_suppliers


class TestLevel3Tools:
    def test_goszakup_search_tool(self):
        result = goszakup_search.invoke({"query": "школа", "limit": 2})
        assert isinstance(result, list)
        assert len(result) > 0

    def test_analyze_tender_tool(self):
        result = analyze_tender.invoke({"tender_id": 10123456})
        assert "tender" in result
        assert "score" in result
        assert "summary" in result

    def test_score_tender_tool(self):
        result = score_tender.invoke({"tender_id": 10123456})
        assert "total_score" in result
        assert "recommendation" in result

    def test_download_tender_docs_tool(self, tmp_path):
        save_dir = str(tmp_path / "docs")
        result = download_tender_docs.invoke({"tender_id": 10123456, "save_path": save_dir})
        assert result["status"] == "downloaded"
        assert Path(result["saved_path"]).exists()

    def test_check_stock_tool(self):
        result = check_stock.invoke({"material_code": "245-1012", "material_name": ""})
        assert result["found"] is True
        assert result["in_stock"] >= 4.0
        assert result["available"] >= 4.0

    def test_check_stock_not_found(self):
        result = check_stock.invoke({"material_code": "999-9999", "material_name": "Несуществующий материал"})
        assert result["found"] is False
        assert result["available"] == 0.0

    def test_batch_check_stock(self):
        materials = [
            {"code": "245-1012", "name": "Арматура А500С d12мм", "quantity": 10.0, "unit": "т"},
            {"code": "101-0300", "name": "Бетон товарный М300", "quantity": 50.0, "unit": "м3"},
        ]
        res = batch_check_stock(materials)
        assert "items" in res
        assert "summary" in res
        assert res["summary"]["total_items"] == 2

    def test_find_supplier_tool(self):
        res = find_supplier.invoke({"material_name": "Арматура", "category": "Металлопрокат"})
        assert res["found"] is True
        assert "КазАрматура" in res["supplier_name"] or "ТОО" in res["supplier_name"]

    def test_create_purchase_order_tool(self):
        res = create_purchase_order.invoke({
            "material_code": "245-1012",
            "material_name": "Арматура А500С d12мм",
            "quantity": 5.0,
            "unit": "т",
            "priority": "URGENT",
        })
        assert res["order_id"].startswith("PO-")
        assert res["quantity"] == 5.5  # 5.0 + 10% safety buffer
        assert res["safety_buffer_pct"] == 10.0
        assert res["priority"] == "URGENT"

    def test_build_purchase_orders_from_stock_check(self):
        stock_items = {
            "245-1012": {
                "code": "245-1012",
                "name": "Арматура А500С d12мм",
                "required": 10.0,
                "available": 2.0,
                "deficit": 8.0,
                "unit": "т",
                "unit_price": 320000.0,
            }
        }
        orders = build_purchase_orders_from_stock_check(stock_items)
        assert len(orders) == 1
        assert orders[0]["order_quantity"] == 8.8  # 8.0 * 1.10
        assert orders[0]["priority"] == "URGENT"  # 8.0 / 10.0 = 80% deficit

    def test_pdf_parser_abc_integration(self):
        fixture_pdf = Path(__file__).resolve().parents[1] / "fixtures" / "abc_pdf" / "sample_statement.pdf"
        if fixture_pdf.exists():
            works = extract_work_list.invoke({"file_path": str(fixture_pdf)})
            materials = extract_materials.invoke({"file_path": str(fixture_pdf)})
            assert len(works) > 0
            assert len(materials) > 0
