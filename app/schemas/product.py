import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    unit: str = Field(default="pcs", max_length=50)
    stock: float = Field(default=0.0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    unit: str | None = Field(default=None, max_length=50)
    stock: float | None = Field(default=None, ge=0)


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ── CSV Import ────────────────────────────────────────────────────────────────

class ImportRowStatus(str, Enum):
    IMPORTED = "imported"
    UPDATED = "updated"
    ERROR = "error"


class ProductImportRowResult(BaseModel):
    row: int
    status: ImportRowStatus
    sku: str | None = None
    name: str | None = None
    reason: str | None = None


class ProductImportResult(BaseModel):
    total_rows: int
    imported: int
    updated: int
    errors: int
    rows: list[ProductImportRowResult]
