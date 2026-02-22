from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.response import Resp, PageResp
from app.models.user import SysUser
from app.models.opportunity import Opportunity, OpportunityFollowUp
from app.schemas.opportunity import (
    OppCreate, OppUpdate, OppOut, OppListItem,
    OppFollowUpCreate, OppFollowUpOut,
)

router = APIRouter(prefix="/opportunities", tags=["商机管理"])


# ── 商机列表 ─────────────────────────────────────────────────
@router.get("", response_model=PageResp[OppListItem])
async def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stage: str | None = None,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    q = select(Opportunity)
    if stage:
        q = q.where(Opportunity.stage == stage)
    if keyword:
        q = q.where(Opportunity.opp_name.ilike(f"%{keyword}%") | Opportunity.company_name.ilike(f"%{keyword}%"))
    q = q.order_by(Opportunity.created_at.desc())

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResp(data=[OppListItem.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)


# ── 创建商机 ─────────────────────────────────────────────────
@router.post("", response_model=Resp[OppOut])
async def create_opportunity(
    body: OppCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    opp = Opportunity(created_by=current_user.id, **body.model_dump())
    db.add(opp)
    await db.commit()
    await db.refresh(opp)
    return Resp.ok(OppOut.model_validate(opp))


# ── 商机详情 ─────────────────────────────────────────────────
@router.get("/{opp_id}", response_model=Resp[OppOut])
async def get_opportunity(
    opp_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    opp = (await db.execute(select(Opportunity).where(Opportunity.id == opp_id))).scalar_one_or_none()
    if not opp:
        raise HTTPException(404, "商机不存在")
    return Resp.ok(OppOut.model_validate(opp))


# ── 更新商机 ─────────────────────────────────────────────────
@router.put("/{opp_id}", response_model=Resp[OppOut])
async def update_opportunity(
    opp_id: str,
    body: OppUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    opp = (await db.execute(select(Opportunity).where(Opportunity.id == opp_id))).scalar_one_or_none()
    if not opp:
        raise HTTPException(404, "商机不存在")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(opp, field, value)
    await db.commit()
    await db.refresh(opp)
    return Resp.ok(OppOut.model_validate(opp))


# ── 删除商机 ─────────────────────────────────────────────────
@router.delete("/{opp_id}", response_model=Resp)
async def delete_opportunity(
    opp_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    opp = (await db.execute(select(Opportunity).where(Opportunity.id == opp_id))).scalar_one_or_none()
    if not opp:
        raise HTTPException(404, "商机不存在")
    await db.delete(opp)
    await db.commit()
    return Resp.ok(message="已删除")


# ── 跟进记录 ─────────────────────────────────────────────────
@router.get("/{opp_id}/follow-ups", response_model=Resp[list[OppFollowUpOut]])
async def list_follow_ups(
    opp_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    rows = (await db.execute(
        select(OpportunityFollowUp)
        .where(OpportunityFollowUp.opp_id == opp_id)
        .order_by(OpportunityFollowUp.created_at.desc())
    )).scalars().all()
    return Resp.ok([OppFollowUpOut.model_validate(r) for r in rows])


@router.post("/{opp_id}/follow-ups", response_model=Resp[OppFollowUpOut])
async def add_follow_up(
    opp_id: str,
    body: OppFollowUpCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    opp = (await db.execute(select(Opportunity).where(Opportunity.id == opp_id))).scalar_one_or_none()
    if not opp:
        raise HTTPException(404, "商机不存在")
    fu = OpportunityFollowUp(opp_id=opp.id, created_by=current_user.id, **body.model_dump())
    db.add(fu)
    await db.commit()
    await db.refresh(fu)
    return Resp.ok(OppFollowUpOut.model_validate(fu))
