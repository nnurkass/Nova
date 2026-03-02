"""
Pydantic data models for goszakup.gov.kz API responses.

Models:
- Tender: main tender record
- TenderLot: individual lot within a tender
- TenderSearchFilter: search parameters
- TenderScore: scoring result for tender evaluation

Implemented in Step 1.3.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TenderLot(BaseModel):
    id: str
    lot_number: int
    name: str
    budget: float
    quantity: float
    unit: str
    delivery_date: Optional[datetime] = None
    description: Optional[str] = None


class Tender(BaseModel):
    id: str
    number: str
    name: str
    budget: float
    status: str
    publish_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    region: Optional[str] = None
    organizer_name: Optional[str] = None
    organizer_bin: Optional[str] = None
    tender_subject: Optional[str] = None
    lots: list[TenderLot] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)


class TenderSearchFilter(BaseModel):
    region: Optional[str] = None
    work_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    status: str = "ACTIVE"
    deadline_from: Optional[datetime] = None
    deadline_to: Optional[datetime] = None
    limit: int = 20


class TenderScore(BaseModel):
    tender_id: str
    budget_score: float
    deadline_score: float
    region_score: float
    purchase_type_score: float
    organizer_history_score: float
    total_score: float
    recommendation: str  # HIGH / MEDIUM / LOW
