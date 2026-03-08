"""Pydantic data models for ABC Smetnie resheniya integration."""
from __future__ import annotations
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


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


class EstimateDocumentMeta(BaseModel):
    source_format: str = "abc_pdf"
    source_file: Optional[str] = None
    project_name: Optional[str] = None
    construction_cipher: Optional[str] = None
    estimate_code: Optional[str] = None
    document_kind: Optional[str] = None
    page_ranges: dict[str, list[int]] = Field(default_factory=dict)


class EstimatePosition(BaseModel):
    position_number: int
    code: str
    name: str
    unit: str
    quantity: float
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    is_work: bool | None = None
    section_name: Optional[str] = None
    source_page: Optional[int] = None
    position_type: Literal["work", "material"] | None = None

    @model_validator(mode="after")
    def sync_position_type(self) -> "EstimatePosition":
        if self.position_type is None and self.is_work is None:
            raise ValueError("Either is_work or position_type must be provided.")

        if self.position_type is None:
            self.position_type = "work" if self.is_work else "material"

        if self.is_work is None:
            self.is_work = self.position_type == "work"

        return self


class ResourceStatement(BaseModel):
    tender_id: Optional[int] = None
    meta: EstimateDocumentMeta | None = None
    positions: list[EstimatePosition] = Field(default_factory=list)
    works: list[ABCWork] = Field(default_factory=list)
    materials: list[ABCMaterial] = Field(default_factory=list)
    total_works_cost: Optional[float] = None
    total_materials_cost: Optional[float] = None
