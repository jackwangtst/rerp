import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Text, ForeignKey, Date, DateTime, func, Numeric, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Contract(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contract"

    contract_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer.id", ondelete="RESTRICT"), nullable=False
    )
    opp_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opportunity.id", ondelete="SET NULL")
    )
    contract_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 新签/续签/变更/补充协议
    certification_standard: Mapped[str] = mapped_column(String(200), nullable=False)
    service_scope: Mapped[str] = mapped_column(Text, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=Decimal("6.00"))
    sign_date: Mapped[date | None] = mapped_column(Date)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="草稿")
    # 草稿/审批中/待签署/执行中/已完成/已终止
    signed_file_url: Mapped[str | None] = mapped_column(String(500))
    sales_person: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="RESTRICT"), nullable=False
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL")
    )
    remark: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL")
    )

    items: Mapped[list["ContractItem"]] = relationship(
        "ContractItem", back_populates="contract", cascade="all, delete-orphan",
        order_by="ContractItem.sort_order"
    )
    payment_plans: Mapped[list["PaymentPlan"]] = relationship(
        "PaymentPlan", back_populates="contract", cascade="all, delete-orphan",
        order_by="PaymentPlan.installment_no"
    )


class ContractItem(Base, UUIDMixin):
    __tablename__ = "contract_item"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contract.id", ondelete="CASCADE"), nullable=False
    )
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    standard: Mapped[str | None] = mapped_column(String(100))
    audit_days: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=Decimal("1"))
    discount: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("1.0000"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    item_type: Mapped[str | None] = mapped_column(String(20))  # 初审/监督审核/再认证
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    contract: Mapped["Contract"] = relationship("Contract", back_populates="items")


class PaymentPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payment_plan"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contract.id", ondelete="CASCADE"), nullable=False
    )
    installment_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))
    plan_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="待支付")
    # 待支付/部分支付/已支付/已逾期

    contract: Mapped["Contract"] = relationship("Contract", back_populates="payment_plans")
    payment_records: Mapped[list["PaymentRecord"]] = relationship(
        "PaymentRecord", back_populates="plan", cascade="all, delete-orphan"
    )


class PaymentRecord(Base, UUIDMixin):
    __tablename__ = "payment_record"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_plan.id", ondelete="RESTRICT"), nullable=False
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contract.id", ondelete="RESTRICT"), nullable=False
    )
    received_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)  # 对公转账/现金/支票/其他
    bank_reference: Mapped[str | None] = mapped_column(String(200))
    received_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="RESTRICT"), nullable=False
    )
    remark: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    plan: Mapped["PaymentPlan"] = relationship("PaymentPlan", back_populates="payment_records")
