"""Pydantic data models for goszakup.gov.kz scraped data."""
from __future__ import annotations
from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel


class TenderLot(BaseModel):
    id: int
    lot_number: int
    name_ru: str
    name_kz: Optional[str] = None
    amount: Optional[float] = None
    count: Optional[float] = None
    unit: Optional[str] = None


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
    lots: list[TenderLot] = []


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
