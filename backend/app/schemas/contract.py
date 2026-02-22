import uuid
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator


# ── 合同服务明细 ─────────────────────────────────────────────
class ContractItemBase(BaseModel):
    item_name: str
    standard: str | None = None
    audit_days: Decimal | None = None
    unit_price: Decimal
    quantity: Decimal = Decimal("1")
    discount: Decimal = Decimal("1.0000")
    amount: Decimal
    item_type: str | None = None
    sort_order: int = 0


class ContractItemOut(ContractItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    contract_id: uuid.UUID


# ── 付款计划 ─────────────────────────────────────────────────
class PaymentPlanBase(BaseModel):
    installment_no: int
    description: str | None = None
    plan_amount: Decimal
    due_date: date | None = None
    status: str = "待支付"


class PaymentPlanOut(PaymentPlanBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    contract_id: uuid.UUID
    created_at: datetime


# ── 收款记录 ─────────────────────────────────────────────────
class PaymentRecordCreate(BaseModel):
    plan_id: uuid.UUID
    received_amount: Decimal
    received_date: date
    payment_method: str
    bank_reference: str | None = None
    remark: str | None = None


class PaymentRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    plan_id: uuid.UUID
    contract_id: uuid.UUID
    received_amount: Decimal
    received_date: date
    payment_method: str
    bank_reference: str | None
    received_by: uuid.UUID
    remark: str | None
    created_at: datetime


# ── 合同 ─────────────────────────────────────────────────────
class ContractBase(BaseModel):
    customer_id: uuid.UUID
    opp_id: uuid.UUID | None = None
    contract_name: str
    contract_type: str
    certification_standard: str
    service_scope: str
    total_amount: Decimal
    tax_rate: Decimal | None = Decimal("6.00")
    sign_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str = "草稿"
    remark: str | None = None
    sales_person: uuid.UUID

    @field_validator("opp_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        if v == "" or v is None:
            return None
        return v


class ContractCreate(ContractBase):
    items: list[ContractItemBase] = []
    payment_plans: list[PaymentPlanBase] = []


class ContractUpdate(BaseModel):
    contract_name: str | None = None
    contract_type: str | None = None
    certification_standard: str | None = None
    service_scope: str | None = None
    total_amount: Decimal | None = None
    tax_rate: Decimal | None = None
    sign_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None
    remark: str | None = None
    sales_person: uuid.UUID | None = None


class ContractOut(ContractBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    contract_no: str
    approved_by: uuid.UUID | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    items: list[ContractItemOut] = []
    payment_plans: list[PaymentPlanOut] = []


class ContractListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    contract_no: str
    customer_id: uuid.UUID
    contract_name: str
    contract_type: str
    certification_standard: str
    total_amount: Decimal
    sign_date: date | None
    start_date: date | None
    end_date: date | None
    status: str
    sales_person: uuid.UUID
    created_at: datetime


# ── 付款计划汇总（全局列表用）────────────────────────────────
class PaymentPlanListItem(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    contract_no: str
    contract_name: str
    installment_no: int
    description: str | None
    plan_amount: Decimal
    due_date: date | None
    status: str
    received_amount: Decimal  # sum of payment records for this plan
    created_at: datetime
