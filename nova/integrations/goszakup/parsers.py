"""HTML parser helpers for public goszakup.gov.kz pages."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from nova.integrations.goszakup.models import Tender, TenderDocument, TenderLot


SEARCH_CARD_SELECTORS = (
    "[data-role='tender-card']",
    ".tender-card",
    "article.announce-item",
    "tr[data-tender-id]",
)
LOT_SELECTORS = (
    "[data-role='tender-lot']",
    ".tender-lot",
    "tr[data-lot-id]",
)
DOCUMENT_SELECTORS = (
    "[data-role='document-item']",
    ".document-item",
    "li.document",
)


def parse_search_results(html: str, *, base_url: str | None = None) -> list[Tender]:
    """Parse a public tender search page into tender models."""
    soup = BeautifulSoup(html, "html.parser")
    tenders: list[Tender] = []

    for node in _find_all_first_match(soup, SEARCH_CARD_SELECTORS):
        tender = _parse_search_card(node, base_url=base_url)
        if tender is not None:
            tenders.append(tender)
    if tenders:
        return tenders

    for row in soup.select("#search-result tbody tr"):
        tender = _parse_search_table_row(row, base_url=base_url)
        if tender is not None:
            tenders.append(tender)
    return tenders


def parse_tender_detail(
    html: str,
    *,
    tender_id: int | None = None,
    base_url: str | None = None,
) -> Tender:
    """Parse a public tender detail page into a single tender model."""
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("[data-role='tender-detail']") or soup
    labels = _extract_label_values(root)

    parsed_id = tender_id or _to_int(
        _first_non_empty(
            _attr(root, "data-tender-id"),
            _text(root.select_one("[data-field='id']")),
            _text(root.select_one("#tender-id")),
            labels.get("номер объявления"),
        )
    )
    if parsed_id is None:
        raise ValueError("Unable to determine tender id from detail page")

    number = _first_non_empty(
        _text(root.select_one("[data-field='number']")),
        _text(root.select_one(".tender-number")),
        labels.get("номер объявления"),
    )
    name_ru = _first_non_empty(
        _text(root.select_one("[data-field='name_ru']")),
        _text(root.select_one("h1")),
        _text(root.select_one(".tender-title")),
        labels.get("наименование объявления"),
    )
    organizer_raw = _first_non_empty(_text(root.select_one("[data-field='organizer_name_ru']")), labels.get("организатор"))
    organizer_bin, organizer_name_from_label = _split_bin_and_name(organizer_raw)
    status_id = _to_int(_text(root.select_one("[data-field='status_id']"))) or 0
    purchase_type_id = _to_int(_text(root.select_one("[data-field='trd_buy_type_id']"))) or 0
    organizer_id = _to_int(_text(root.select_one("[data-field='organizer_id']"))) or 0
    organizer_bin = _first_non_empty(_text(root.select_one("[data-field='organizer_bin']")), organizer_bin, "")
    organizer_name = _first_non_empty(
        _text(root.select_one("[data-field='organizer_name_ru']")),
        _text(root.select_one(".organizer-name")),
        organizer_name_from_label,
        "",
    )

    if not number or not name_ru:
        raise ValueError("Tender detail page does not contain required number/name fields")

    return Tender(
        id=parsed_id,
        number=number,
        name_ru=name_ru,
        name_kz=_text(root.select_one("[data-field='name_kz']")),
        status_id=status_id,
        trd_buy_type_id=purchase_type_id,
        organizer_id=organizer_id,
        organizer_bin=organizer_bin,
        organizer_name_ru=organizer_name,
        publish_date=_parse_datetime(
            _first_non_empty(
                _text(root.select_one("[data-field='publish_date']")),
                labels.get("дата публикации объявления"),
            )
        ),
        start_date=_parse_datetime(
            _first_non_empty(
                _text(root.select_one("[data-field='start_date']")),
                labels.get("срок начала приема заявок"),
            )
        ),
        end_date=_parse_datetime(
            _first_non_empty(
                _text(root.select_one("[data-field='end_date']")),
                labels.get("срок окончания приема заявок"),
            )
        ),
        total_sum=_parse_float(
            _first_non_empty(
                _text(root.select_one("[data-field='total_sum']")),
                labels.get("сумма закупки"),
            )
        ),
        customer_bin=_text(root.select_one("[data-field='customer_bin']")),
        customer_name_ru=_first_non_empty(_text(root.select_one("[data-field='customer_name_ru']")), labels.get("заказчик")),
        ref_region_id=_to_int(_text(root.select_one("[data-field='ref_region_id']"))),
        detail_url=_resolve_url(
            base_url,
            _first_non_empty(_attr(root, "data-detail-url"), _attr(root.select_one("link[rel='canonical']"), "href")),
        ),
        status_name_ru=_first_non_empty(
            _text(root.select_one("[data-field='status_name_ru']")),
            labels.get("статус объявления"),
        ),
        purchase_type_name_ru=_first_non_empty(
            _text(root.select_one("[data-field='purchase_type_name_ru']")),
            labels.get("способ проведения закупки"),
            labels.get("тип закупки"),
        ),
        technical_specification=_normalize_text(_text(root.select_one("[data-field='technical_specification']"))),
        documents=parse_documents(root, base_url=base_url),
        lots=parse_lots(root),
    )


def parse_lots(node: Tag) -> list[TenderLot]:
    """Extract tender lots from the provided node."""
    lots: list[TenderLot] = []
    for lot_node in _find_all_first_match(node, LOT_SELECTORS):
        lot_id = _to_int(_first_non_empty(_attr(lot_node, "data-lot-id"), _text(lot_node.select_one("[data-field='id']"))))
        lot_number = _to_int(
            _first_non_empty(_attr(lot_node, "data-lot-number"), _text(lot_node.select_one("[data-field='lot_number']")))
        )
        name_ru = _first_non_empty(
            _text(lot_node.select_one("[data-field='name_ru']")),
            _text(lot_node.select_one(".lot-name")),
        )
        if lot_id is None or lot_number is None or not name_ru:
            continue
        lots.append(
            TenderLot(
                id=lot_id,
                lot_number=lot_number,
                name_ru=name_ru,
                name_kz=_text(lot_node.select_one("[data-field='name_kz']")),
                amount=_parse_float(_text(lot_node.select_one("[data-field='amount']"))),
                count=_parse_float(_text(lot_node.select_one("[data-field='count']"))),
                unit=_text(lot_node.select_one("[data-field='unit']")),
            )
        )
    return lots


def parse_documents(node: Tag, *, base_url: str | None = None) -> list[TenderDocument]:
    """Extract tender documents from the provided node."""
    documents: list[TenderDocument] = []
    for index, doc_node in enumerate(_find_all_first_match(node, DOCUMENT_SELECTORS), start=1):
        doc_id = _to_int(_first_non_empty(_attr(doc_node, "data-document-id"), _text(doc_node.select_one("[data-field='id']"))))
        link = doc_node.select_one("a[href]")
        url = _resolve_url(base_url, _attr(link, "href"))
        name = _first_non_empty(
            _text(doc_node.select_one("[data-field='name']")),
            _text(link),
        )
        if not url or not name:
            continue
        documents.append(
            TenderDocument(
                id=doc_id or index,
                name=name,
                url=url,
                category=_text(doc_node.select_one("[data-field='category']")),
                published_at=_parse_datetime(_text(doc_node.select_one("[data-field='published_at']"))),
            )
        )
    return documents


def _parse_search_card(node: Tag, *, base_url: str | None = None) -> Tender | None:
    tender_id = _to_int(_first_non_empty(_attr(node, "data-tender-id"), _text(node.select_one("[data-field='id']"))))
    number = _first_non_empty(_text(node.select_one("[data-field='number']")), _text(node.select_one(".tender-number")))
    name_ru = _first_non_empty(_text(node.select_one("[data-field='name_ru']")), _text(node.select_one(".tender-title")))
    if tender_id is None or not number or not name_ru:
        return None

    return Tender(
        id=tender_id,
        number=number,
        name_ru=name_ru,
        name_kz=_text(node.select_one("[data-field='name_kz']")),
        status_id=_to_int(_text(node.select_one("[data-field='status_id']"))) or 0,
        trd_buy_type_id=_to_int(_text(node.select_one("[data-field='trd_buy_type_id']"))) or 0,
        organizer_id=_to_int(_text(node.select_one("[data-field='organizer_id']"))) or 0,
        organizer_bin=_first_non_empty(_text(node.select_one("[data-field='organizer_bin']")), ""),
        organizer_name_ru=_first_non_empty(_text(node.select_one("[data-field='organizer_name_ru']")), ""),
        publish_date=_parse_datetime(_text(node.select_one("[data-field='publish_date']"))),
        start_date=_parse_datetime(_text(node.select_one("[data-field='start_date']"))),
        end_date=_parse_datetime(_text(node.select_one("[data-field='end_date']"))),
        total_sum=_parse_float(_text(node.select_one("[data-field='total_sum']"))),
        customer_bin=_text(node.select_one("[data-field='customer_bin']")),
        customer_name_ru=_text(node.select_one("[data-field='customer_name_ru']")),
        ref_region_id=_to_int(_text(node.select_one("[data-field='ref_region_id']"))),
        detail_url=_resolve_url(base_url, _attr(node.select_one("a[href]"), "href")),
        status_name_ru=_text(node.select_one("[data-field='status_name_ru']")),
        purchase_type_name_ru=_text(node.select_one("[data-field='purchase_type_name_ru']")),
    )


def _parse_search_table_row(row: Tag, *, base_url: str | None = None) -> Tender | None:
    cells = row.find_all("td", recursive=False)
    if len(cells) < 7:
        return None

    link = cells[1].select_one("a[href]")
    detail_url = _resolve_url(base_url, _attr(link, "href"))
    number = _first_non_empty(_text(cells[0].select_one("strong")), _text(cells[0]))
    name_ru = _first_non_empty(_text(link), _text(cells[1]))
    tender_id = _to_int(_attr(link, "href")) or _to_int(number)
    organizer_bin, organizer_name = _split_bin_and_name(_strip_labeled_prefix(_text(cells[1].select_one("small")), "Организатор:"))

    if tender_id is None or not number or not name_ru:
        return None

    publish_date = _parse_datetime(_text(cells[3]))
    end_date = _parse_datetime(_text(cells[4]))
    return Tender(
        id=tender_id,
        number=number,
        name_ru=name_ru,
        status_id=0,
        trd_buy_type_id=0,
        organizer_id=0,
        organizer_bin=organizer_bin or "",
        organizer_name_ru=organizer_name or "",
        publish_date=publish_date,
        start_date=publish_date,
        end_date=end_date,
        total_sum=_parse_float(_text(cells[5])),
        detail_url=detail_url,
        status_name_ru=_text(cells[6]),
        purchase_type_name_ru=_text(cells[2]),
    )


def _find_all_first_match(node: Tag | BeautifulSoup, selectors: Iterable[str]) -> list[Tag]:
    for selector in selectors:
        matches = node.select(selector)
        if matches:
            return [match for match in matches if isinstance(match, Tag)]
    return []


def _text(node: Tag | None) -> str | None:
    if node is None:
        return None
    return _normalize_text(node.get_text(" ", strip=True))


def _attr(node: Tag | None, name: str) -> str | None:
    if node is None:
        return None
    value = node.get(name)
    if not isinstance(value, str):
        return None
    return value.strip() or None


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    return normalized or None


def _strip_labeled_prefix(value: str | None, prefix: str) -> str | None:
    normalized = _normalize_text(value)
    if normalized is None:
        return None
    if normalized.startswith(prefix):
        return normalized[len(prefix) :].strip()
    return normalized


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.replace("\u00a0", "").replace(" ", "").replace("₸", "")
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return None
    return int(digits)


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    candidates = (
        value,
        value.replace("Z", "+00:00"),
        value.replace(".", "-"),
    )
    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    for fmt in ("%d.%m.%Y %H:%M", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _extract_label_values(root: Tag | BeautifulSoup) -> dict[str, str]:
    values: dict[str, str] = {}

    for group in root.select(".form-group"):
        label = _normalize_text(_text(group.select_one("label")))
        if label is None:
            continue
        value = _attr(group.select_one("input[value]"), "value") or _text(group.select_one(".form-control"))
        if value:
            values[label.lower()] = value

    for row in root.select("table tr"):
        header = _normalize_text(_text(row.find("th")))
        value = _normalize_text(_text(row.find("td")))
        if header and value:
            values[header.lower()] = value

    return values


def _split_bin_and_name(value: str | None) -> tuple[str | None, str | None]:
    normalized = _normalize_text(value)
    if normalized is None:
        return None, None
    parts = normalized.split(" ", 1)
    if parts and parts[0].isdigit() and len(parts[0]) >= 8:
        return parts[0], parts[1] if len(parts) > 1 else None
    return None, normalized


def _resolve_url(base_url: str | None, value: str | None) -> str | None:
    if value is None:
        return None
    if base_url is None:
        return value
    return urljoin(base_url.rstrip("/") + "/", value.lstrip("/"))


__all__ = [
    "parse_documents",
    "parse_lots",
    "parse_search_results",
    "parse_tender_detail",
]
