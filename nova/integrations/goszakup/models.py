"""Pydantic data models for parsed goszakup.gov.kz tender data."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TenderLot(BaseModel):
    id: int
    lot_number: int
    name_ru: str
    name_kz: Optional[str] = None
    amount: Optional[float] = None
    count: Optional[float] = None
    unit: Optional[str] = None


class TenderDocument(BaseModel):
    id: int
    name: str
    url: str
    category: Optional[str] = None
    published_at: Optional[datetime] = None


class Tender(BaseModel):
    id: int
    number: str
    name_ru: str
    name_kz: Optional[str] = None
    status_id: int
    trd_buy_type_id: int
    organizer_id: int
    organizer_bin: str
    organizer_name_ru: str
    publish_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_sum: Optional[float] = None
    customer_bin: Optional[str] = None
    customer_name_ru: Optional[str] = None
    ref_region_id: Optional[int] = None
    detail_url: Optional[str] = None
    status_name_ru: Optional[str] = None
    purchase_type_name_ru: Optional[str] = None
    technical_specification: Optional[str] = None
    documents: list[TenderDocument] = Field(default_factory=list)
    lots: list[TenderLot] = Field(default_factory=list)


class TenderSearchFilter(BaseModel):
    region: Optional[str] = None
    region_id: Optional[int] = None
    work_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    deadline_from: Optional[datetime] = None
    limit: int = 10


class TenderScore(BaseModel):
    tender_id: int
    total_score: float
    budget_score: float
    deadline_score: float
    region_score: float
    purchase_type_score: float
    history_score: float
    recommendation: Literal["HIGH", "MEDIUM", "LOW"]


__all__ = [
    "Tender",
    "TenderDocument",
    "TenderLot",
    "TenderScore",
    "TenderSearchFilter",
]
