from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.response import Resp, PageResp
from app.core.notify import notify_task
from app.models.user import SysUser
from app.models.project import CertProject, ProjectTask
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectOut, ProjectListItem,
    TaskCreate, TaskUpdate, TaskOut, TaskListItem,
)

router = APIRouter(prefix="/projects", tags=["任务管理"])


def _next_project_no(seq_val: int, year: int) -> str:
    return f"CP-{year}-{seq_val:04d}"


# ── 认证项目列表 ─────────────────────────────────────────────
@router.get("", response_model=PageResp[ProjectListItem])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    customer_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    q = select(CertProject)
    if status:
        q = q.where(CertProject.status == status)
    if keyword:
        q = q.where(
            CertProject.standard.ilike(f"%{keyword}%") |
            CertProject.project_no.ilike(f"%{keyword}%") |
            CertProject.certification_scope.ilike(f"%{keyword}%")
        )
    if customer_id:
        q = q.where(CertProject.customer_id == customer_id)
    q = q.order_by(CertProject.created_at.desc())

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResp(data=[ProjectListItem.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)


# ── 创建认证项目 ─────────────────────────────────────────────
@router.post("", response_model=Resp[ProjectOut])
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    from datetime import datetime
    year = datetime.now().year
    seq = (await db.execute(select(func.nextval("seq_project_no")))).scalar()

    project = CertProject(
        project_no=_next_project_no(seq, year),
        **body.model_dump(),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return Resp.ok(ProjectOut.model_validate(project))


# ── 项目详情 ─────────────────────────────────────────────────
@router.get("/{project_id}", response_model=Resp[ProjectOut])
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    project = (await db.execute(select(CertProject).where(CertProject.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(404, "项目不存在")
    return Resp.ok(ProjectOut.model_validate(project))


# ── 更新认证项目 ─────────────────────────────────────────────
@router.put("/{project_id}", response_model=Resp[ProjectOut])
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    project = (await db.execute(select(CertProject).where(CertProject.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(404, "项目不存在")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return Resp.ok(ProjectOut.model_validate(project))


# ── 删除认证项目 ─────────────────────────────────────────────
@router.delete("/{project_id}", response_model=Resp)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    project = (await db.execute(select(CertProject).where(CertProject.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(404, "项目不存在")
    await db.delete(project)
    await db.commit()
    return Resp.ok(message="已删除")


# ── 项目下的任务列表 ─────────────────────────────────────────
@router.get("/{project_id}/tasks", response_model=Resp[list[TaskOut]])
async def list_project_tasks(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    rows = (await db.execute(
        select(ProjectTask)
        .where(ProjectTask.project_id == project_id)
        .order_by(ProjectTask.planned_start)
    )).scalars().all()
    return Resp.ok([TaskOut.model_validate(r) for r in rows])


# ── 全局任务列表 ─────────────────────────────────────────────
router_tasks = APIRouter(prefix="/tasks", tags=["任务管理"])


@router_tasks.get("", response_model=PageResp[TaskListItem])
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    assigned_to: str | None = None,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    q = select(ProjectTask)
    if status:
        q = q.where(ProjectTask.status == status)
    if assigned_to:
        q = q.where(ProjectTask.assigned_to == assigned_to)
    if keyword:
        q = q.where(ProjectTask.task_name.ilike(f"%{keyword}%"))
    q = q.order_by(ProjectTask.planned_start.asc())

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResp(data=[TaskListItem.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)


@router_tasks.post("", response_model=Resp[TaskOut])
async def create_task(
    body: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    task = ProjectTask(created_by=current_user.id, **body.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)

    project = (await db.execute(
        select(CertProject).where(CertProject.id == task.project_id)
    )).scalar_one_or_none()

    await notify_task(
        task_name=task.task_name,
        project_no=project.project_no if project else str(task.project_id),
        assigned_to=current_user.full_name or current_user.username,
        planned_end=task.planned_end.strftime("%Y-%m-%d"),
    )

    return Resp.ok(TaskOut.model_validate(task))


@router_tasks.put("/{task_id}", response_model=Resp[TaskOut])
async def update_task(
    task_id: str,
    body: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    task = (await db.execute(select(ProjectTask).where(ProjectTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "任务不存在")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return Resp.ok(TaskOut.model_validate(task))


@router_tasks.delete("/{task_id}", response_model=Resp)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    task = (await db.execute(select(ProjectTask).where(ProjectTask.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(404, "任务不存在")
    await db.delete(task)
    await db.commit()
    return Resp.ok(message="已删除")
