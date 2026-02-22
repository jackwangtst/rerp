import uuid
from sqlalchemy import String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Customer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "customer"

    customer_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    company_short_name: Mapped[str | None] = mapped_column(String(100))
    unified_social_credit_code: Mapped[str | None] = mapped_column(String(20), unique=True)
    legal_representative: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    company_size: Mapped[str | None] = mapped_column(String(10))   # 小微/中/大
    province: Mapped[str | None] = mapped_column(String(50))
    city: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(500))
    customer_level: Mapped[str | None] = mapped_column(String(1))  # A/B/C
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="潜在")
    assigned_sales: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL"))
    source_opp_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    remark: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL"))

    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="customer", cascade="all, delete-orphan")
    follow_ups: Mapped[list["CustomerFollowUp"]] = relationship("CustomerFollowUp", back_populates="customer", cascade="all, delete-orphan")


class Contact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contact"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100))
    wechat: Mapped[str | None] = mapped_column(String(100))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="contacts")


class CustomerFollowUp(Base, UUIDMixin):
    __tablename__ = "customer_follow_up"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    follow_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 电话/拜访/邮件/微信/其他
    content: Mapped[str] = mapped_column(Text, nullable=False)
    next_date: Mapped[str | None] = mapped_column(String(20))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="SET NULL"))

    from sqlalchemy import DateTime, func
    from datetime import datetime
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="follow_ups")
