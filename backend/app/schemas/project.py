import uuid
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, field_validator


# ── 认证项目 ─────────────────────────────────────────────────
class ProjectBase(BaseModel):
    contract_id: uuid.UUID
    customer_id: uuid.UUID
    standard: str
    certification_scope: str
    phase: str = "初审"
    project_manager: uuid.UUID
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    status: str = "筹备中"
    progress: int = 0


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    standard: str | None = None
    certification_scope: str | None = None
    phase: str | None = None
    project_manager: uuid.UUID | None = None
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_end_date: date | None = None
    status: str | None = None
    progress: int | None = None


class ProjectListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_no: str
    contract_id: uuid.UUID
    customer_id: uuid.UUID
    standard: str
    certification_scope: str
    phase: str
    project_manager: uuid.UUID
    planned_start_date: date | None
    planned_end_date: date | None
    actual_end_date: date | None
    progress: int
    status: str
    created_at: datetime


class ProjectOut(ProjectListItem):
    updated_at: datetime


# ── 审核任务 ─────────────────────────────────────────────────
class TaskBase(BaseModel):
    task_name: str
    task_type: str
    description: str | None = None
    assigned_to: uuid.UUID
    co_auditors: list[uuid.UUID] = []
    priority: str = "普通"
    planned_start: datetime
    planned_end: datetime
    status: str = "待开始"

    @field_validator("planned_start", "planned_end", mode="before")
    @classmethod
    def parse_dt(cls, v: object) -> object:
        if v == "" or v is None:
            return None
        return v


class TaskCreate(TaskBase):
    project_id: uuid.UUID


class TaskUpdate(BaseModel):
    task_name: str | None = None
    task_type: str | None = None
    description: str | None = None
    assigned_to: uuid.UUID | None = None
    priority: str | None = None
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    actual_hours: float | None = None
    status: str | None = None
    result: str | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    task_name: str
    task_type: str
    description: str | None
    assigned_to: uuid.UUID
    co_auditors: list[uuid.UUID]
    priority: str
    planned_start: datetime
    planned_end: datetime
    actual_start: datetime | None
    actual_end: datetime | None
    actual_hours: float | None
    status: str
    result: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TaskListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    task_name: str
    task_type: str
    assigned_to: uuid.UUID
    priority: str
    planned_start: datetime
    planned_end: datetime
    actual_start: datetime | None
    actual_end: datetime | None
    status: str
    created_at: datetime
