import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Text, ForeignKey, Date, DateTime, func, Numeric, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Opportunity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "opportunity"

    opp_name: Mapped[str] = mapped_column(String(200), nullable=False)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lead.id", ondelete="SET NULL")
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer.id", ondelete="SET NULL")
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    stage: Mapped[str] = mapped_column(String(20), nullable=False, default="初步接触")
    # 初步接触/需求确认/报价/谈判/赢单/输单
    certification_type: Mapped[str] = mapped_column(String(200), nullable=False)
    estimated_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    expected_close_date: Mapped[date | None] = mapped_column(Date)
    win_probability: Mapped[int | None] = mapped_column(SmallInteger)
    competitor: Mapped[str | None] = mapped_column(String(200))
    loss_reason: Mapped[str | None] = mapped_column(Text)
    assigned_to: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="RESTRICT"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL")
    )

    follow_ups: Mapped[list["OpportunityFollowUp"]] = relationship(
        "OpportunityFollowUp", back_populates="opportunity", cascade="all, delete-orphan"
    )


class OpportunityFollowUp(Base, UUIDMixin):
    __tablename__ = "opportunity_follow_up"

    opp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opportunity.id", ondelete="CASCADE"), nullable=False
    )
    follow_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    next_date: Mapped[str | None] = mapped_column(String(20))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    opportunity: Mapped["Opportunity"] = relationship("Opportunity", back_populates="follow_ups")
