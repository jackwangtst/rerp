import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Text, ForeignKey, Date, DateTime, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin


class Invoice(Base, UUIDMixin):
    """发票管理"""
    __tablename__ = "invoice"

    # 关联收款（可选，也支持单独开票）
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotation_payment.id", ondelete="SET NULL")
    )
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quote_no: Mapped[str | None] = mapped_column(String(50))

    # 发票信息
    invoice_type: Mapped[str] = mapped_column(String(20), nullable=False, default="增值税普通发票")
    # 增值税普通发票 / 增值税专用发票
    invoice_title: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_no: Mapped[str | None] = mapped_column(String(50))
    invoice_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    invoice_no: Mapped[str | None] = mapped_column(String(100))
    issue_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="待开具")
    # 待开具 / 已开具 / 已邮寄 / 已上传
    remark: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    payment: Mapped["QuotationPayment | None"] = relationship("QuotationPayment")  # type: ignore[name-defined]
