from __future__ import annotations
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


EXPENSE_TYPES = ["认证费", "差旅", "代理费", "测试费", "其他"]


class ExpenseBase(BaseModel):
    quotation_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    expense_type: str
    amount: Decimal
    vendor: str | None = None
    paid_at: date
    remark: str | None = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    quotation_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    expense_type: str | None = None
    amount: Decimal | None = None
    vendor: str | None = None
    paid_at: date | None = None
    remark: str | None = None


class ExpenseOut(ExpenseBase):
    id: uuid.UUID
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    quote_no: str | None = None
    customer_name: str | None = None
    creator_name: str | None = None

    model_config = {"from_attributes": True}


class ExpenseListItem(BaseModel):
    id: uuid.UUID
    expense_type: str
    amount: Decimal
    vendor: str | None
    paid_at: date
    quotation_id: uuid.UUID | None
    quote_no: str | None
    customer_id: uuid.UUID | None
    customer_name: str | None
    remark: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
