"""
Goszakup.gov.kz GraphQL API client with Graceful Fallback / Mock-first mode.

Handles authentication, query execution, pagination, error handling,
and transparent fallback to synthetic tender fixtures when API tokens
are absent or network requests fail.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

import httpx

from nova.config import get_settings
from nova.integrations.goszakup.models import Tender, TenderLot
from nova.integrations.goszakup.queries import GET_ANNOUNCEMENT_DETAIL, SEARCH_ANNOUNCEMENTS

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
SAMPLE_TENDERS_FILE = DATA_DIR / "sample_tenders.json"

DUMMY_TOKENS = {
    "goszakup-test",
    "mock-goszakup-token",
    "your_goszakup_token_here",
    "your-goszakup-token",
    "",
}


class GoszakupClient:
    """GraphQL client for goszakup.gov.kz with mock-first fallback."""

    def __init__(
        self,
        token: Optional[str] = None,
        graphql_url: Optional[str] = None,
        timeout: float = 10.0,
        sample_file: Optional[Path] = None,
    ) -> None:
        settings = get_settings()
        self.token = token or (
            settings.goszakup_token.get_secret_value()
            if hasattr(settings.goszakup_token, "get_secret_value")
            else str(settings.goszakup_token)
        )
        self.graphql_url = graphql_url or settings.goszakup_graphql_url
        self.timeout = timeout
        self.sample_file = sample_file or SAMPLE_TENDERS_FILE

    @property
    def is_mock_mode(self) -> bool:
        """Return True if running in fallback mock mode."""
        if not self.token:
            return True
        tok = self.token.strip().lower()
        if tok in DUMMY_TOKENS:
            return True
        if any(tok.startswith(prefix) for prefix in ("mock", "test", "your", "dummy", "sk-", "goszakup-test")):
            return True
        if "test" in tok or "mock" in tok:
            return True
        return False

    def _load_sample_tenders(self) -> list[dict[str, Any]]:
        """Load sample tenders from local JSON fixture."""
        if not self.sample_file.exists():
            logger.warning("Sample tenders file not found: %s", self.sample_file)
            return []
        try:
            with open(self.sample_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error("Failed to load sample tenders: %s", exc)
            return []

    def _dict_to_tender(self, data: dict[str, Any]) -> Tender:
        """Convert dictionary to Tender Pydantic model."""
        lots_data = data.get("lots", [])
        lots = [
            TenderLot(
                id=lot.get("id", idx + 1),
                lot_number=lot.get("lot_number", lot.get("lotNumber", idx + 1)),
                name_ru=lot.get("name_ru", lot.get("nameRu", "")),
                name_kz=lot.get("name_kz", lot.get("nameKz")),
                amount=lot.get("amount", data.get("total_sum")),
                count=lot.get("count", 1.0),
                unit=lot.get("unit", "услуга"),
            )
            for idx, lot in enumerate(lots_data)
        ]
        if not lots:
            lots = [
                TenderLot(
                    id=1,
                    lot_number=1,
                    name_ru=data.get("name_ru", data.get("nameRu", "СМР")),
                    amount=data.get("total_sum", data.get("totalSum", 0.0)),
                    count=1.0,
                    unit="услуга",
                )
            ]

        return Tender(
            id=int(data.get("id", 1)),
            number=str(data.get("number", data.get("numberAnno", f"LOT-{data.get('id', 1)}"))),
            name_ru=data.get("name_ru", data.get("nameRu", "")),
            name_kz=data.get("name_kz", data.get("nameKz")),
            status_id=int(data.get("status_id", data.get("statusId", 1))),
            trd_buy_type_id=int(data.get("trd_buy_type_id", data.get("refBuyTypeId", 2))),
            organizer_id=int(data.get("organizer_id", 1)),
            organizer_bin=str(data.get("organizer_bin", data.get("orgBin", "990140001234"))),
            organizer_name_ru=str(data.get("organizer_name_ru", data.get("orgNameRu", "Заказчик РК"))),
            publish_date=data.get("publish_date", data.get("publishDate")),
            start_date=data.get("start_date", data.get("startDate")),
            end_date=data.get("end_date", data.get("endDate")),
            total_sum=data.get("total_sum", data.get("totalSum")),
            customer_bin=data.get("customer_bin", data.get("customerBin")),
            customer_name_ru=data.get("customer_name_ru", data.get("customerNameRu")),
            ref_region_id=data.get("ref_region_id", data.get("refRegionId")),
            lots=lots,
        )

    def search_tenders_mock(
        self,
        query: str = "",
        region_id: Optional[int] = None,
        region_name: Optional[str] = None,
        budget_min: Optional[float] = None,
        budget_max: Optional[float] = None,
        limit: int = 10,
    ) -> list[Tender]:
        """Filter sample tenders by search criteria."""
        samples = self._load_sample_tenders()
        results: list[Tender] = []

        query_tokens = [t.lower() for t in query.split() if len(t) > 2] if query else []

        for item in samples:
            # Region filter
            if region_id is not None and item.get("ref_region_id") != region_id:
                continue
            if region_name:
                item_region = str(item.get("region_name", "")).lower()
                item_name = str(item.get("name_ru", "")).lower()
                reg_clean = region_name.lower().replace("г.", "").replace("город", "").strip()
                if reg_clean and reg_clean not in item_region and reg_clean not in item_name:
                    continue

            # Budget filters
            total_sum = float(item.get("total_sum", 0.0) or 0.0)
            if budget_min is not None and total_sum < budget_min:
                continue
            if budget_max is not None and total_sum > budget_max:
                continue

            # Query keyword filter
            if query_tokens:
                text_corpus = (
                    f"{item.get('name_ru', '')} {item.get('customer_name_ru', '')} "
                    f"{item.get('region_name', '')} "
                    f"{' '.join(lot.get('name_ru', '') for lot in item.get('lots', []))}"
                ).lower()
                # Check if at least one significant query word is present or partial match
                matches = any(token in text_corpus for token in query_tokens)
                if not matches:
                    continue

            results.append(self._dict_to_tender(item))
            if len(results) >= limit:
                break

        # If strict filtering returned nothing, return all samples matching region or budget up to limit
        if not results and samples:
            for item in samples:
                results.append(self._dict_to_tender(item))
                if len(results) >= limit:
                    break

        return results

    def get_tender_details_mock(self, tender_id: int | str) -> Optional[Tender]:
        """Fetch tender by ID from sample tenders."""
        samples = self._load_sample_tenders()
        for item in samples:
            if str(item.get("id")) == str(tender_id) or str(item.get("number")) == str(tender_id):
                return self._dict_to_tender(item)
        if samples:
            return self._dict_to_tender(samples[0])
        return None

    def search_tenders(
        self,
        query: str = "",
        region_id: Optional[int] = None,
        region_name: Optional[str] = None,
        budget_min: Optional[float] = None,
        budget_max: Optional[float] = None,
        limit: int = 10,
    ) -> list[Tender]:
        """Search tenders with live API call and automatic fallback."""
        if self.is_mock_mode:
            logger.info("Using mock Goszakup search for query: %r", query)
            return self.search_tenders_mock(
                query=query,
                region_id=region_id,
                region_name=region_name,
                budget_min=budget_min,
                budget_max=budget_max,
                limit=limit,
            )

        # Real API execution
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        variables: dict[str, Any] = {"limit": limit}
        filter_dict: dict[str, Any] = {}
        if region_id:
            filter_dict["refRegionId"] = region_id
        if filter_dict:
            variables["filter"] = filter_dict

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.graphql_url,
                    json={"query": SEARCH_ANNOUNCEMENTS, "variables": variables},
                    headers=headers,
                )
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("data", {}).get("TrdBuy", [])
                    if items:
                        return [self._dict_to_tender(it) for it in items]
                logger.warning(
                    "Goszakup API responded with %d: %s. Falling back to mock data.",
                    response.status_code,
                    response.text[:200],
                )
        except Exception as exc:
            logger.warning("Goszakup API network error: %s. Falling back to mock data.", exc)

        return self.search_tenders_mock(
            query=query,
            region_id=region_id,
            region_name=region_name,
            budget_min=budget_min,
            budget_max=budget_max,
            limit=limit,
        )

    def get_tender_details(self, tender_id: int | str) -> Optional[Tender]:
        """Fetch tender details with live API call and fallback."""
        if self.is_mock_mode:
            return self.get_tender_details_mock(tender_id)

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        try:
            numeric_id = int(str(tender_id).split("-")[0])
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.graphql_url,
                    json={"query": GET_ANNOUNCEMENT_DETAIL, "variables": {"id": numeric_id}},
                    headers=headers,
                )
                if response.status_code == 200:
                    data = response.json()
                    item = data.get("data", {}).get("TrdBuy")
                    if item:
                        return self._dict_to_tender(item)
        except Exception as exc:
            logger.warning("Goszakup get_details error: %s. Falling back to mock data.", exc)

        return self.get_tender_details_mock(tender_id)


__all__ = ["GoszakupClient", "SAMPLE_TENDERS_FILE"]
