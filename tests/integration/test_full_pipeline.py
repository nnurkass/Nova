"""Integration tests for the full end-to-end multi-agent pipeline."""
from nova.graph.main_graph import run_pipeline


class TestFullPipeline:
    def test_pipeline_runs_end_to_end_almaty_school(self):
        task = "Поиск тендеров на капремонт школ в г. Алматы"
        final_state = run_pipeline(task)

        assert final_state["errors"] == []
        assert final_state["metadata"]["visited_nodes"] == ["coo", "procurement", "pto", "supply"]
        assert final_state["metadata"]["supply_completed"] is True
        assert final_state["selected_tender"] is not None
        assert "школ" in final_state["selected_tender"].name_ru.lower() or final_state["selected_tender"].total_sum > 0
        assert len(final_state["work_list"]) > 0
        assert len(final_state["materials_list"]) > 0
        assert "items" in final_state["stock_check"]
        assert len(final_state["purchase_orders"]) > 0

        # Check executive summary report
        report = final_state["metadata"].get("final_report", "")
        assert report != ""
        assert "NOVA — ИСПОЛНИТЕЛЬНЫЙ ОТЧЁТ" in report
        assert "ФИНАНСОВЫЙ БАЛАНС" in report

    def test_pipeline_runs_astana_water_network(self):
        task = "Строительство наружных сетей водоснабжения в Астане"
        final_state = run_pipeline(task)

        assert final_state["errors"] == []
        assert final_state["selected_tender"] is not None
        assert len(final_state["purchase_orders"]) > 0
        assert any("труб" in po["name"].lower() or "арматур" in po["name"].lower() for po in final_state["purchase_orders"])
