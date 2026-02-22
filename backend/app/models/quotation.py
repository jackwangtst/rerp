import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Text, ForeignKey, Date, DateTime, func, Numeric, SmallInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Quotation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "quotation"

    opp_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opportunity.id", ondelete="RESTRICT"), nullable=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer.id", ondelete="SET NULL"), nullable=True
    )
    quote_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    items: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # items 结构:
    # {
    #   "country": "沙特阿拉伯",
    #   "name": "SASO认证",        # 认证名称
    #   "standard": "IEC 62368-1", # 认证标准
    #   "cb_required": "Y",        # 是否需要CB
    #   "local_testing": "N",      # 是否本地测试
    #   "models": "2款型号",        # 型号/证书数量
    #   "months": 3,               # 认证周期（月）
    #   "unit_price": 8000,
    #   "discount": 1.0,
    #   "amount": 8000
    # }
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    discount_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="草稿")
    # 草稿/待审批/已发送/已接受/已拒绝/已过期
    contact_name: Mapped[str | None] = mapped_column(String(50))
    contact_phone: Mapped[str | None] = mapped_column(String(30))
    deliver_to_address: Mapped[str | None] = mapped_column(Text)
    product_name: Mapped[str | None] = mapped_column(String(200))   # 产品名称
    product_model: Mapped[str | None] = mapped_column(String(200))  # 产品型号
    payment_terms: Mapped[str | None] = mapped_column(Text)
    remark: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL")
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL")
    )

    opportunity: Mapped["Opportunity"] = relationship("Opportunity")  # type: ignore[name-defined]
    customer: Mapped["Customer"] = relationship("Customer")  # type: ignore[name-defined]
