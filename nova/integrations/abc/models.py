"""Pydantic data models for ABC Smetnie resheniya integration."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ABCWork(BaseModel):
    code: str
    name: str
    unit: str
    quantity: float
    price: Optional[float] = None


class ABCMaterial(BaseModel):
    code: str
    name: str
    unit: str
    quantity: float
    price: Optional[float] = None


class ResourceStatement(BaseModel):
    tender_id: Optional[int] = None
    works: list[ABCWork] = []
    materials: list[ABCMaterial] = []
    total_works_cost: Optional[float] = None
    total_materials_cost: Optional[float] = None


class EstimatePosition(BaseModel):
    position_number: int
    code: str
    name: str
    unit: str
    quantity: float
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    is_work: bool
