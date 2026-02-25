from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.response import Resp, PageResp
from app.models.user import SysUser
from app.models.expense import Expense
from app.models.contract import Contract
from app.models.customer import Customer
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseOut, ExpenseListItem

router = APIRouter(prefix="/expenses", tags=["支出管理"])


def _to_list_item(e: Expense) -> ExpenseListItem:
    return ExpenseListItem(
        id=e.id,
        expense_type=e.expense_type,
        amount=e.amount,
        vendor=e.vendor,
        paid_at=e.paid_at,
        contract_id=e.contract_id,
        contract_no=e.contract.contract_no if e.contract else None,
        customer_id=e.customer_id,
        customer_name=e.customer.name if e.customer else None,
        remark=e.remark,
        created_at=e.created_at,
    )


def _to_out(e: Expense) -> ExpenseOut:
    out = ExpenseOut.model_validate(e)
    out.contract_no = e.contract.contract_no if e.contract else None
    out.customer_name = e.customer.name if e.customer else None
    out.creator_name = e.creator.full_name if e.creator else None
    return out


# ── 列表 ─────────────────────────────────────────────────────
@router.get("", response_model=PageResp[ExpenseListItem])
async def list_expenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    expense_type: str | None = None,
    customer_id: str | None = None,
    contract_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload
    q = select(Expense).options(
        selectinload(Expense.contract),
        selectinload(Expense.customer),
    )
    if expense_type:
        q = q.where(Expense.expense_type == expense_type)
    if customer_id:
        q = q.where(Expense.customer_id == customer_id)
    if contract_id:
        q = q.where(Expense.contract_id == contract_id)
    if date_from:
        q = q.where(Expense.paid_at >= date_from)
    if date_to:
        q = q.where(Expense.paid_at <= date_to)
    q = q.order_by(Expense.paid_at.desc())

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResp(data=[_to_list_item(r) for r in rows], total=total, page=page, page_size=page_size)


# ── 统计（利润分析） ───────────────────────────────────────────
@router.get("/stats", response_model=Resp)
async def expense_stats(
    date_from: date | None = None,
    date_to: date | None = None,
    customer_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    from sqlalchemy import and_
    from app.models.contract import PaymentRecord

    exp_q = select(func.sum(Expense.amount))
    rev_q = select(func.sum(PaymentRecord.received_amount))

    filters_exp = []
    filters_rev = []
    if date_from:
        filters_exp.append(Expense.paid_at >= date_from)
        filters_rev.append(PaymentRecord.paid_at >= date_from)
    if date_to:
        filters_exp.append(Expense.paid_at <= date_to)
        filters_rev.append(PaymentRecord.paid_at <= date_to)
    if customer_id:
        filters_exp.append(Expense.customer_id == customer_id)
        # 通过 contract 关联 customer
        rev_q = rev_q.join(Contract, PaymentRecord.contract_id == Contract.id)
        filters_rev.append(Contract.customer_id == customer_id)

    if filters_exp:
        exp_q = exp_q.where(and_(*filters_exp))
    if filters_rev:
        rev_q = rev_q.where(and_(*filters_rev))

    total_expense = (await db.execute(exp_q)).scalar() or 0
    total_revenue = (await db.execute(rev_q)).scalar() or 0
    profit = float(total_revenue) - float(total_expense)
    profit_rate = round(profit / float(total_revenue) * 100, 2) if total_revenue else 0

    # 按支出类型汇总
    type_q = select(Expense.expense_type, func.sum(Expense.amount).label("total"))
    if filters_exp:
        type_q = type_q.where(and_(*filters_exp))
    type_q = type_q.group_by(Expense.expense_type)
    type_rows = (await db.execute(type_q)).all()
    by_type = {r.expense_type: float(r.total) for r in type_rows}

    return Resp.ok({
        "total_expense": float(total_expense),
        "total_revenue": float(total_revenue),
        "profit": profit,
        "profit_rate": profit_rate,
        "by_type": by_type,
    })


# ── 创建 ─────────────────────────────────────────────────────
@router.post("", response_model=Resp[ExpenseOut])
async def create_expense(
    body: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload
    e = Expense(**body.model_dump(), created_by=user.id)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    # reload with relations
    e = (await db.execute(
        select(Expense).options(
            selectinload(Expense.contract),
            selectinload(Expense.customer),
            selectinload(Expense.creator),
        ).where(Expense.id == e.id)
    )).scalar_one()
    return Resp.ok(_to_out(e))


# ── 更新 ─────────────────────────────────────────────────────
@router.put("/{expense_id}", response_model=Resp[ExpenseOut])
async def update_expense(
    expense_id: str,
    body: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload
    e = (await db.execute(select(Expense).where(Expense.id == expense_id))).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(e, k, v)
    await db.commit()
    e = (await db.execute(
        select(Expense).options(
            selectinload(Expense.contract),
            selectinload(Expense.customer),
            selectinload(Expense.creator),
        ).where(Expense.id == e.id)
    )).scalar_one()
    return Resp.ok(_to_out(e))


# ── 删除 ─────────────────────────────────────────────────────
@router.delete("/{expense_id}", response_model=Resp)
async def delete_expense(
    expense_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    e = (await db.execute(select(Expense).where(Expense.id == expense_id))).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    await db.delete(e)
    await db.commit()
    return Resp.ok()
