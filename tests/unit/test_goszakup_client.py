"""Unit tests for GoszakupClient in live and mock/fallback modes."""
from nova.integrations.goszakup.client import GoszakupClient
from nova.integrations.goszakup.models import Tender


class TestGoszakupClient:
    def test_client_initialization_mock_mode(self):
        client = GoszakupClient(token="mock-token")
        assert client.is_mock_mode is True

    def test_search_tenders_fallback_returns_tenders(self):
        client = GoszakupClient(token="goszakup-test")
        tenders = client.search_tenders(query="школа", limit=5)
        assert len(tenders) > 0
        assert all(isinstance(t, Tender) for t in tenders)
        assert any("школ" in t.name_ru.lower() for t in tenders)

    def test_search_tenders_region_filter(self):
        client = GoszakupClient(token="goszakup-test")
        almaty_tenders = client.search_tenders(region_name="Алматы", limit=5)
        assert len(almaty_tenders) > 0
        assert any(t.ref_region_id == 750000000 or "алматы" in t.name_ru.lower() for t in almaty_tenders)

    def test_get_tender_details_fallback(self):
        client = GoszakupClient(token="goszakup-test")
        tender = client.get_tender_details(10123456)
        assert tender is not None
        assert isinstance(tender, Tender)
        assert tender.id == 10123456
        assert len(tender.lots) >= 1

    def test_search_tenders_budget_filter(self):
        client = GoszakupClient(token="goszakup-test")
        tenders = client.search_tenders(budget_min=200_000_000, limit=5)
        assert len(tenders) > 0
        assert all(t.total_sum >= 200_000_000 for t in tenders)
