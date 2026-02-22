import uuid
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


# ── 线索跟进记录 ─────────────────────────────────────────────
class LeadFollowUpCreate(BaseModel):
    follow_type: str
    content: str
    next_date: str | None = None


class LeadFollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    lead_id: uuid.UUID
    follow_type: str
    content: str
    next_date: str | None
    created_by: uuid.UUID | None
    created_at: datetime


# ── 线索 ─────────────────────────────────────────────────────
class LeadBase(BaseModel):
    company_name: str
    contact_name: str | None = None
    contact_phone: str
    contact_email: str | None = None
    source: str
    industry: str | None = None
    province: str | None = None
    city: str | None = None
    certification_interest: str | None = None
    status: str = "待跟进"
    assigned_to: uuid.UUID | None = None
    next_follow_up_date: date | None = None
    remark: str | None = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    company_name: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    source: str | None = None
    industry: str | None = None
    province: str | None = None
    city: str | None = None
    certification_interest: str | None = None
    status: str | None = None
    assigned_to: uuid.UUID | None = None
    next_follow_up_date: date | None = None
    remark: str | None = None


class LeadOut(LeadBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class LeadListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    company_name: str
    contact_name: str | None
    contact_phone: str
    source: str
    industry: str | None
    province: str | None
    city: str | None
    certification_interest: str | None
    status: str
    assigned_to: uuid.UUID | None
    next_follow_up_date: date | None
    created_at: datetime
