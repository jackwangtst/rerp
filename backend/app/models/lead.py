import uuid
from datetime import datetime, date
from sqlalchemy import String, Text, ForeignKey, Date, DateTime, func, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Lead(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "lead"

    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(100))
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(30), nullable=False)  # 展会/网络/转介绍/电话/其他
    industry: Mapped[str | None] = mapped_column(String(100))
    province: Mapped[str | None] = mapped_column(String(50))
    city: Mapped[str | None] = mapped_column(String(50))
    certification_interest: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="待跟进")
    # 待跟进/跟进中/已转化/已放弃
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL")
    )
    next_follow_up_date: Mapped[date | None] = mapped_column(Date)
    remark: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL")
    )

    follow_ups: Mapped[list["LeadFollowUp"]] = relationship(
        "LeadFollowUp", back_populates="lead", cascade="all, delete-orphan"
    )


class LeadFollowUp(Base, UUIDMixin):
    __tablename__ = "lead_follow_up"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lead.id", ondelete="CASCADE"), nullable=False
    )
    follow_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 电话/拜访/邮件/微信/其他
    content: Mapped[str] = mapped_column(Text, nullable=False)
    next_date: Mapped[str | None] = mapped_column(String(20))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lead: Mapped["Lead"] = relationship("Lead", back_populates="follow_ups")
