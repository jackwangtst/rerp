import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ── 联系人 ──────────────────────────────────────────────────
class ContactBase(BaseModel):
    name: str
    title: str | None = None
    department: str | None = None
    phone: str
    email: str | None = None
    wechat: str | None = None
    is_primary: bool = False


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    name: str | None = None
    title: str | None = None
    department: str | None = None
    phone: str | None = None
    email: str | None = None
    wechat: str | None = None
    is_primary: bool | None = None


class ContactOut(ContactBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    customer_id: uuid.UUID
    created_at: datetime


# ── 跟进记录 ────────────────────────────────────────────────
class FollowUpCreate(BaseModel):
    follow_type: str
    content: str
    next_date: str | None = None


class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    customer_id: uuid.UUID
    follow_type: str
    content: str
    next_date: str | None
    created_by: uuid.UUID | None
    created_at: datetime


# ── 客户 ────────────────────────────────────────────────────
class CustomerBase(BaseModel):
    company_name: str
    company_short_name: str | None = None
    unified_social_credit_code: str | None = None
    legal_representative: str | None = None
    industry: str | None = None
    company_size: str | None = None
    province: str | None = None
    city: str | None = None
    address: str | None = None
    customer_level: str | None = None
    status: str = "潜在"
    assigned_sales: uuid.UUID | None = None
    remark: str | None = None


class CustomerCreate(CustomerBase):
    contacts: list[ContactCreate] = []


class CustomerUpdate(BaseModel):
    company_name: str | None = None
    company_short_name: str | None = None
    unified_social_credit_code: str | None = None
    legal_representative: str | None = None
    industry: str | None = None
    company_size: str | None = None
    province: str | None = None
    city: str | None = None
    address: str | None = None
    customer_level: str | None = None
    status: str | None = None
    assigned_sales: uuid.UUID | None = None
    remark: str | None = None
    contacts: list[ContactCreate] | None = None


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    customer_no: str
    created_at: datetime
    contacts: list[ContactOut] = []


class CustomerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    customer_no: str
    company_name: str
    company_short_name: str | None
    industry: str | None
    company_size: str | None
    province: str | None
    city: str | None
    customer_level: str | None
    status: str
    assigned_sales: uuid.UUID | None
    created_at: datetime
