from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.response import Resp, PageResp
from app.models.user import SysUser
from app.models.lead import Lead, LeadFollowUp
from app.schemas.lead import (
    LeadCreate, LeadUpdate, LeadOut, LeadListItem,
    LeadFollowUpCreate, LeadFollowUpOut,
)

router = APIRouter(prefix="/leads", tags=["线索管理"])


# ── 线索列表 ─────────────────────────────────────────────────
@router.get("", response_model=PageResp[LeadListItem])
async def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    q = select(Lead)
    if status:
        q = q.where(Lead.status == status)
    if keyword:
        q = q.where(Lead.company_name.ilike(f"%{keyword}%"))
    q = q.order_by(Lead.created_at.desc())

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResp(data=[LeadListItem.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)


# ── 创建线索 ─────────────────────────────────────────────────
@router.post("", response_model=Resp[LeadOut])
async def create_lead(
    body: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    lead = Lead(created_by=current_user.id, **body.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return Resp.ok(LeadOut.model_validate(lead))


# ── 线索详情 ─────────────────────────────────────────────────
@router.get("/{lead_id}", response_model=Resp[LeadOut])
async def get_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    lead = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "线索不存在")
    return Resp.ok(LeadOut.model_validate(lead))


# ── 更新线索 ─────────────────────────────────────────────────
@router.put("/{lead_id}", response_model=Resp[LeadOut])
async def update_lead(
    lead_id: str,
    body: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    lead = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "线索不存在")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    await db.commit()
    await db.refresh(lead)
    return Resp.ok(LeadOut.model_validate(lead))


# ── 删除线索 ─────────────────────────────────────────────────
@router.delete("/{lead_id}", response_model=Resp)
async def delete_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    lead = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "线索不存在")
    await db.delete(lead)
    await db.commit()
    return Resp.ok(message="已删除")


# ── 跟进记录 ─────────────────────────────────────────────────
@router.get("/{lead_id}/follow-ups", response_model=Resp[list[LeadFollowUpOut]])
async def list_follow_ups(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    rows = (await db.execute(
        select(LeadFollowUp)
        .where(LeadFollowUp.lead_id == lead_id)
        .order_by(LeadFollowUp.created_at.desc())
    )).scalars().all()
    return Resp.ok([LeadFollowUpOut.model_validate(r) for r in rows])


@router.post("/{lead_id}/follow-ups", response_model=Resp[LeadFollowUpOut])
async def add_follow_up(
    lead_id: str,
    body: LeadFollowUpCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    lead = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "线索不存在")
    fu = LeadFollowUp(lead_id=lead.id, created_by=current_user.id, **body.model_dump())
    db.add(fu)
    await db.commit()
    await db.refresh(fu)
    return Resp.ok(LeadFollowUpOut.model_validate(fu))
