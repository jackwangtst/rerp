import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PriceCatalogBase(BaseModel):
    country: str | None = None
    name: str
    cert_type: str | None = None
    sample_qty: int | None = None
    based_on_report: str | None = None
    lead_weeks: int | None = None
    includes_testing: str | None = None
    cert_validity_years: int | None = None
    series_apply: str | None = None
    ref_price: Decimal | None = None
    remark: str | None = None


class PriceCatalogCreate(PriceCatalogBase):
    pass


class PriceCatalogUpdate(BaseModel):
    country: str | None = None
    name: str | None = None
    cert_type: str | None = None
    sample_qty: int | None = None
    based_on_report: str | None = None
    lead_weeks: int | None = None
    includes_testing: str | None = None
    cert_validity_years: int | None = None
    series_apply: str | None = None
    ref_price: Decimal | None = None
    remark: str | None = None


class PriceCatalogOut(PriceCatalogBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PriceCatalogSearchItem(BaseModel):
    """报价明细搜索下拉用，返回所有可带入字段"""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    country: str | None
    name: str
    based_on_report: str | None
    lead_weeks: int | None
    includes_testing: str | None
    series_apply: str | None
    ref_price: Decimal | None
