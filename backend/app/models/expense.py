import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy import String, Text, ForeignKey, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Expense(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "expense"

    contract_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contract.id", ondelete="SET NULL")
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer.id", ondelete="SET NULL")
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cert_project.id", ondelete="SET NULL")
    )
    expense_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(100))
    paid_at: Mapped[date] = mapped_column(Date, nullable=False)
    remark: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL")
    )

    contract = relationship("Contract", foreign_keys=[contract_id], lazy="select")
    customer = relationship("Customer", foreign_keys=[customer_id], lazy="select")
    creator = relationship("User", foreign_keys=[created_by], lazy="select")
