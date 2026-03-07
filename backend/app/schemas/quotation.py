import uuid
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class QuotationItem(BaseModel):
    country: str | None = None          # 国家
    name: str                           # 认证名称/项目
    standard: str | None = None         # 认证标准
    lr_or_not: str | None = None        # 是否需要当地代表LR: Y/N
    local_testing: str | None = None    # 是否本地测试: Y/N
    models: str | None = None           # 型号/证书数量描述
    weeks: int | None = None            # 认证周期（周）
    unit_price: Decimal
    discount: Decimal = Decimal("1.0")
    amount: Decimal
    item_remark: str | None = None      # 明细备注


class QuotationBase(BaseModel):
    opp_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    items: list[QuotationItem] = []
    total_amount: Decimal
    discount_amount: Decimal | None = None
    discount_rate: Decimal | None = None
    valid_until: date
    status: str = "草稿"
    contact_name: str | None = None
    contact_phone: str | None = None
    deliver_to_address: str | None = None
    product_name: str | None = None
    product_model: str | None = None
    payment_terms: str | None = None
    remark: str | None = None


class QuotationCreate(QuotationBase):
    pass


class QuotationUpdate(BaseModel):
    opp_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    items: list[QuotationItem] | None = None
    total_amount: Decimal | None = None
    discount_amount: Decimal | None = None
    discount_rate: Decimal | None = None
    valid_until: date | None = None
    status: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    deliver_to_address: str | None = None
    product_name: str | None = None
    product_model: str | None = None
    payment_terms: str | None = None
    remark: str | None = None


class QuotationOut(QuotationBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    quote_no: str
    version: int
    created_by: uuid.UUID | None
    approved_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class QuotationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    quote_no: str
    opp_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    version: int
    total_amount: Decimal
    discount_amount: Decimal | None
    discount_rate: Decimal | None
    valid_until: date
    status: str
    created_by: uuid.UUID | None
    created_at: datetime
