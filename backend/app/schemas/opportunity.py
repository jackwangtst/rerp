import uuid
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


# ── 商机跟进记录 ─────────────────────────────────────────────
class OppFollowUpCreate(BaseModel):
    follow_type: str
    content: str
    next_date: str | None = None


class OppFollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    opp_id: uuid.UUID
    follow_type: str
    content: str
    next_date: str | None
    created_by: uuid.UUID | None
    created_at: datetime


# ── 商机 ─────────────────────────────────────────────────────
class OppBase(BaseModel):
    opp_name: str
    lead_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    company_name: str
    stage: str = "初步接触"
    certification_type: str
    estimated_amount: Decimal | None = None
    expected_close_date: date | None = None
    win_probability: int | None = None
    competitor: str | None = None
    loss_reason: str | None = None
    assigned_to: uuid.UUID


class OppCreate(OppBase):
    pass


class OppUpdate(BaseModel):
    opp_name: str | None = None
    lead_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    company_name: str | None = None
    stage: str | None = None
    certification_type: str | None = None
    estimated_amount: Decimal | None = None
    expected_close_date: date | None = None
    win_probability: int | None = None
    competitor: str | None = None
    loss_reason: str | None = None
    assigned_to: uuid.UUID | None = None


class OppOut(OppBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class OppListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    opp_name: str
    company_name: str
    stage: str
    certification_type: str
    estimated_amount: Decimal | None
    expected_close_date: date | None
    win_probability: int | None
    assigned_to: uuid.UUID
    lead_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    created_at: datetime
