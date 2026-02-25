import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Text, ForeignKey, Date, DateTime, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin


class QuotationPayment(Base, UUIDMixin):
    __tablename__ = "quotation_payment"

    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotation.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer.id", ondelete="SET NULL")
    )
    quote_no: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(200))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    received_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="待收款")
    # 待收款 / 部分收款 / 已收款
    received_date: Mapped[date | None] = mapped_column(Date)
    payment_method: Mapped[str | None] = mapped_column(String(20))
    remark: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    quotation: Mapped["Quotation"] = relationship("Quotation")  # type: ignore[name-defined]
