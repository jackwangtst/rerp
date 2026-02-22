import uuid
from datetime import datetime, date
from sqlalchemy import String, Text, ForeignKey, Date, DateTime, SmallInteger, func, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class CertProject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cert_project"

    project_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contract.id", ondelete="RESTRICT"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer.id", ondelete="RESTRICT"), nullable=False
    )
    standard: Mapped[str] = mapped_column(String(200), nullable=False)
    certification_scope: Mapped[str] = mapped_column(Text, nullable=False)
    phase: Mapped[str] = mapped_column(String(20), nullable=False, default="初审")
    # 初审/监督审核/再认证
    project_manager: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="RESTRICT"), nullable=False
    )
    planned_start_date: Mapped[date | None] = mapped_column(Date)
    planned_end_date: Mapped[date | None] = mapped_column(Date)
    actual_end_date: Mapped[date | None] = mapped_column(Date)
    progress: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="筹备中")
    # 筹备中/进行中/已完成/已取消

    tasks: Mapped[list["ProjectTask"]] = relationship(
        "ProjectTask", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectTask(Base, UUIDMixin):
    __tablename__ = "task"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cert_project.id", ondelete="CASCADE"), nullable=False
    )
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    task_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # 文件审查/现场审核/报告编写/其他
    description: Mapped[str | None] = mapped_column(Text)
    assigned_to: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="RESTRICT"), nullable=False
    )
    co_auditors: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list
    )
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="普通")
    # 紧急/高/普通/低
    planned_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_hours: Mapped[float | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="待开始")
    # 待开始/进行中/已完成/已取消
    result: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sys_user.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped["CertProject"] = relationship("CertProject", back_populates="tasks")
