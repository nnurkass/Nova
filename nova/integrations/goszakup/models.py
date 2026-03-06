"""Pydantic data models for goszakup.gov.kz API responses."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TenderDocument(BaseModel):
    id: int
    file_path: Optional[str] = None
    original_name: Optional[str] = None
    name_ru: Optional[str] = None
    name_kz: Optional[str] = None
    url: Optional[str] = None


class TenderContract(BaseModel):
    id: int
    trd_buy_id: Optional[int] = None
    announcement_number: Optional[str] = None
    contract_number: Optional[str] = None
    status_id: Optional[int] = None
    supplier_biin: Optional[str] = None
    sign_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    amount: Optional[float] = None
    documents: list[TenderDocument] = Field(default_factory=list)


class TenderLot(BaseModel):
    id: int
    lot_number: int
    name_ru: str
    name_kz: Optional[str] = None
    description_ru: Optional[str] = None
    description_kz: Optional[str] = None
    amount: Optional[float] = None
    count: Optional[float] = None
    unit: Optional[str] = None
    trd_buy_id: Optional[int] = None
    documents: list[TenderDocument] = Field(default_factory=list)


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
    status_name_ru: Optional[str] = None
    purchase_type_name_ru: Optional[str] = None
    description_ru: Optional[str] = None
    description_kz: Optional[str] = None
    technical_specification: Optional[str] = None
    source_url: Optional[str] = None
    documents: list[TenderDocument] = Field(default_factory=list)
    contracts: list[TenderContract] = Field(default_factory=list)
    lots: list[TenderLot] = Field(default_factory=list)


class TenderSearchFilter(BaseModel):
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
    "TenderContract",
    "TenderDocument",
    "TenderLot",
    "TenderScore",
    "TenderSearchFilter",
]
