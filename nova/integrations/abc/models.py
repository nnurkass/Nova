"""
Pydantic data models for ABC Smetnie resheniya integration.

Models:
- ABCWork: work item from resource statement
- ABCMaterial: material entry
- ResourceStatement: full resource statement document
- EstimatePosition: position in estimate

Implemented in Step 1.3.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ABCWork(BaseModel):
    code: str
    name: str
    unit: str
    quantity: float
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    chapter: Optional[str] = None
    section: Optional[str] = None


class ABCMaterial(BaseModel):
    code: str
    name: str
    unit: str
    quantity: float
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    supplier: Optional[str] = None


class ResourceStatement(BaseModel):
    id: Optional[str] = None
    name: str
    project_name: Optional[str] = None
    created_at: Optional[datetime] = None
    works: list[ABCWork] = Field(default_factory=list)
    materials: list[ABCMaterial] = Field(default_factory=list)
    total_cost: Optional[float] = None


class EstimatePosition(BaseModel):
    position_number: int
    code: str
    name: str
    unit: str
    quantity: float
    unit_price: float
    total_price: float
    type: Literal["work", "material", "machine"]
