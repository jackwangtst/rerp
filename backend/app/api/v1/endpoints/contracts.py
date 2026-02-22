from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.response import Resp, PageResp
from app.core.notify import notify_contract
from app.models.user import SysUser
from app.models.contract import Contract, ContractItem, PaymentPlan, PaymentRecord
from app.schemas.contract import (
    ContractCreate, ContractUpdate, ContractOut, ContractListItem,
    PaymentPlanOut, PaymentPlanListItem, PaymentRecordCreate, PaymentRecordOut,
)

router = APIRouter(prefix="/contracts", tags=["合同管理"])


def _next_contract_no(seq_val: int, year: int) -> str:
    return f"HT-{year}-{seq_val:04d}"


def _load_contract_q(contract_id: str):
    return (
        select(Contract)
        .options(
            selectinload(Contract.items),
            selectinload(Contract.payment_plans),
        )
        .where(Contract.id == contract_id)
    )


# ── 合同列表 ─────────────────────────────────────────────────
@router.get("", response_model=PageResp[ContractListItem])
async def list_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    customer_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    q = select(Contract)
    if status:
        q = q.where(Contract.status == status)
    if keyword:
        q = q.where(Contract.contract_name.ilike(f"%{keyword}%") | Contract.contract_no.ilike(f"%{keyword}%"))
    if customer_id:
        q = q.where(Contract.customer_id == customer_id)
    q = q.order_by(Contract.created_at.desc())

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResp(data=[ContractListItem.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)


# ── 创建合同 ─────────────────────────────────────────────────
@router.post("", response_model=Resp[ContractOut])
async def create_contract(
    body: ContractCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    from datetime import datetime
    year = datetime.now().year
    seq = (await db.execute(select(func.nextval("seq_contract_no")))).scalar()

    contract = Contract(
        contract_no=_next_contract_no(seq, year),
        created_by=current_user.id,
        **body.model_dump(exclude={"items", "payment_plans"}),
    )
    db.add(contract)
    await db.flush()

    for i, item in enumerate(body.items):
        db.add(ContractItem(contract_id=contract.id, sort_order=i, **item.model_dump(exclude={"sort_order"})))

    for plan in body.payment_plans:
        db.add(PaymentPlan(contract_id=contract.id, **plan.model_dump()))

    await db.commit()

    result = await db.execute(_load_contract_q(str(contract.id)))
    out = ContractOut.model_validate(result.scalar_one())

    await notify_contract(
        contract_no=out.contract_no,
        contract_name=out.contract_name,
        amount=float(out.total_amount),
        creator=current_user.full_name or current_user.username,
    )

    return Resp.ok(out)


# ── 合同详情 ─────────────────────────────────────────────────
@router.get("/{contract_id}", response_model=Resp[ContractOut])
async def get_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    result = await db.execute(_load_contract_q(contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(404, "合同不存在")
    return Resp.ok(ContractOut.model_validate(contract))


# ── 更新合同基本信息 ─────────────────────────────────────────
@router.put("/{contract_id}", response_model=Resp[ContractOut])
async def update_contract(
    contract_id: str,
    body: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    result = await db.execute(_load_contract_q(contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(404, "合同不存在")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(contract, field, value)
    await db.commit()
    result2 = await db.execute(_load_contract_q(contract_id))
    return Resp.ok(ContractOut.model_validate(result2.scalar_one()))


# ── 删除合同 ─────────────────────────────────────────────────
@router.delete("/{contract_id}", response_model=Resp)
async def delete_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    contract = (await db.execute(select(Contract).where(Contract.id == contract_id))).scalar_one_or_none()
    if not contract:
        raise HTTPException(404, "合同不存在")
    await db.delete(contract)
    await db.commit()
    return Resp.ok(message="已删除")


# ── 付款计划 ─────────────────────────────────────────────────
@router.get("/{contract_id}/payment-plans", response_model=Resp[list[PaymentPlanOut]])
async def list_payment_plans(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    rows = (await db.execute(
        select(PaymentPlan)
        .where(PaymentPlan.contract_id == contract_id)
        .order_by(PaymentPlan.installment_no)
    )).scalars().all()
    return Resp.ok([PaymentPlanOut.model_validate(r) for r in rows])


# ── 收款记录 ─────────────────────────────────────────────────
@router.get("/{contract_id}/payment-records", response_model=Resp[list[PaymentRecordOut]])
async def list_payment_records(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    rows = (await db.execute(
        select(PaymentRecord)
        .where(PaymentRecord.contract_id == contract_id)
        .order_by(PaymentRecord.received_date.desc())
    )).scalars().all()
    return Resp.ok([PaymentRecordOut.model_validate(r) for r in rows])


@router.post("/{contract_id}/payment-records", response_model=Resp[PaymentRecordOut])
async def add_payment_record(
    contract_id: str,
    body: PaymentRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    contract = (await db.execute(select(Contract).where(Contract.id == contract_id))).scalar_one_or_none()
    if not contract:
        raise HTTPException(404, "合同不存在")
    record = PaymentRecord(
        contract_id=contract.id,
        received_by=current_user.id,
        **body.model_dump(),
    )
    db.add(record)

    # Update payment plan status
    plan = (await db.execute(select(PaymentPlan).where(PaymentPlan.id == body.plan_id))).scalar_one_or_none()
    if plan:
        plan.status = "已支付"

    await db.commit()
    await db.refresh(record)
    return Resp.ok(PaymentRecordOut.model_validate(record))


# ── 全局付款计划汇总列表 ──────────────────────────────────────
@router.get("/payment-plans/all", response_model=PageResp[PaymentPlanListItem])
async def list_all_payment_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    overdue: bool | None = None,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    """Return all payment plans across all contracts, enriched with contract info and received amount."""
    today = date.today()

    # Subquery: sum of received_amount per plan
    received_sq = (
        select(
            PaymentRecord.plan_id,
            func.coalesce(func.sum(PaymentRecord.received_amount), 0).label("received_amount"),
        )
        .group_by(PaymentRecord.plan_id)
        .subquery()
    )

    q = (
        select(
            PaymentPlan.id,
            PaymentPlan.contract_id,
            Contract.contract_no,
            Contract.contract_name,
            PaymentPlan.installment_no,
            PaymentPlan.description,
            PaymentPlan.plan_amount,
            PaymentPlan.due_date,
            PaymentPlan.status,
            PaymentPlan.created_at,
            func.coalesce(received_sq.c.received_amount, 0).label("received_amount"),
        )
        .join(Contract, Contract.id == PaymentPlan.contract_id)
        .outerjoin(received_sq, received_sq.c.plan_id == PaymentPlan.id)
    )

    if status:
        q = q.where(PaymentPlan.status == status)
    if overdue is True:
        q = q.where(PaymentPlan.due_date < today, PaymentPlan.status.notin_(["已支付"]))
    if keyword:
        q = q.where(
            Contract.contract_name.ilike(f"%{keyword}%") | Contract.contract_no.ilike(f"%{keyword}%")
        )

    q = q.order_by(PaymentPlan.due_date.asc())

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).mappings().all()

    items = [
        PaymentPlanListItem(
            id=r["id"],
            contract_id=r["contract_id"],
            contract_no=r["contract_no"],
            contract_name=r["contract_name"],
            installment_no=r["installment_no"],
            description=r["description"],
            plan_amount=r["plan_amount"],
            due_date=r["due_date"],
            status=r["status"],
            received_amount=r["received_amount"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
    return PageResp(data=items, total=total, page=page, page_size=page_size)

