from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.response import Resp, PageResp
from app.models.user import SysUser
from app.models.customer import Customer, Contact, CustomerFollowUp
from app.schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerOut, CustomerListItem,
    ContactCreate, ContactUpdate, ContactOut,
    FollowUpCreate, FollowUpOut,
)

router = APIRouter(prefix="/customers", tags=["客户管理"])


def _next_customer_no(seq_val: int, year: int) -> str:
    return f"CU-{year}-{seq_val:04d}"


# ── 客户列表 ────────────────────────────────────────────────
@router.get("", response_model=PageResp[CustomerListItem])
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    status: str | None = None,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    q = select(Customer)
    if status:
        q = q.where(Customer.status == status)
    if keyword:
        q = q.where(Customer.company_name.ilike(f"%{keyword}%"))
    q = q.order_by(Customer.created_at.desc())

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResp(data=[CustomerListItem.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)


# ── 创建客户 ────────────────────────────────────────────────
@router.post("", response_model=Resp[CustomerOut])
async def create_customer(
    body: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    from datetime import datetime
    year = datetime.now().year
    seq = (await db.execute(select(func.nextval("seq_customer_no")))).scalar()
    data = body.model_dump(exclude={"contacts"})
    # 空字符串统一转 null，避免唯一约束冲突
    for field in ("unified_social_credit_code", "company_short_name", "legal_representative",
                  "industry", "company_size", "province", "city", "address",
                  "customer_level", "remark"):
        if data.get(field) == "":
            data[field] = None
    customer = Customer(
        customer_no=_next_customer_no(seq, year),
        created_by=current_user.id,
        **data,
    )
    db.add(customer)
    await db.flush()

    for c in body.contacts:
        db.add(Contact(customer_id=customer.id, **c.model_dump()))

    await db.commit()
    await db.refresh(customer)

    result = await db.execute(
        select(Customer).options(selectinload(Customer.contacts)).where(Customer.id == customer.id)
    )
    return Resp.ok(CustomerOut.model_validate(result.scalar_one()))


# ── 客户详情 ────────────────────────────────────────────────
@router.get("/{customer_id}", response_model=Resp[CustomerOut])
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Customer).options(selectinload(Customer.contacts)).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(404, "客户不存在")
    return Resp.ok(CustomerOut.model_validate(customer))


# ── 更新客户 ────────────────────────────────────────────────
@router.put("/{customer_id}", response_model=Resp[CustomerOut])
async def update_customer(
    customer_id: str,
    body: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Customer).options(selectinload(Customer.contacts)).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(404, "客户不存在")
    data = body.model_dump(exclude_unset=True, exclude={"contacts"})
    for field in ("unified_social_credit_code", "company_short_name", "legal_representative",
                  "industry", "company_size", "province", "city", "address",
                  "customer_level", "remark"):
        if data.get(field) == "":
            data[field] = None
    for field, value in data.items():
        setattr(customer, field, value)
    if body.contacts is not None:
        for c in list(customer.contacts):
            await db.delete(c)
        await db.flush()
        for c in body.contacts:
            db.add(Contact(customer_id=customer.id, **c.model_dump()))
    await db.commit()
    await db.refresh(customer)
    result2 = await db.execute(
        select(Customer).options(selectinload(Customer.contacts)).where(Customer.id == customer_id)
    )
    return Resp.ok(CustomerOut.model_validate(result2.scalar_one()))


# ── 删除客户 ────────────────────────────────────────────────
@router.delete("/{customer_id}", response_model=Resp)
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    customer = (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none()
    if not customer:
        raise HTTPException(404, "客户不存在")
    await db.delete(customer)
    await db.commit()
    return Resp.ok(message="已删除")


# ── 联系人 ──────────────────────────────────────────────────
@router.post("/{customer_id}/contacts", response_model=Resp[ContactOut])
async def add_contact(
    customer_id: str,
    body: ContactCreate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    customer = (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none()
    if not customer:
        raise HTTPException(404, "客户不存在")
    contact = Contact(customer_id=customer.id, **body.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return Resp.ok(ContactOut.model_validate(contact))


@router.put("/{customer_id}/contacts/{contact_id}", response_model=Resp[ContactOut])
async def update_contact(
    customer_id: str,
    contact_id: str,
    body: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    contact = (await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.customer_id == customer_id)
    )).scalar_one_or_none()
    if not contact:
        raise HTTPException(404, "联系人不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(contact, field, value)
    await db.commit()
    await db.refresh(contact)
    return Resp.ok(ContactOut.model_validate(contact))


@router.delete("/{customer_id}/contacts/{contact_id}", response_model=Resp)
async def delete_contact(
    customer_id: str,
    contact_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    contact = (await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.customer_id == customer_id)
    )).scalar_one_or_none()
    if not contact:
        raise HTTPException(404, "联系人不存在")
    await db.delete(contact)
    await db.commit()
    return Resp.ok(message="已删除")


# ── 跟进记录 ────────────────────────────────────────────────
@router.get("/{customer_id}/follow-ups", response_model=Resp[list[FollowUpOut]])
async def list_follow_ups(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    rows = (await db.execute(
        select(CustomerFollowUp)
        .where(CustomerFollowUp.customer_id == customer_id)
        .order_by(CustomerFollowUp.created_at.desc())
    )).scalars().all()
    return Resp.ok([FollowUpOut.model_validate(r) for r in rows])


@router.post("/{customer_id}/follow-ups", response_model=Resp[FollowUpOut])
async def add_follow_up(
    customer_id: str,
    body: FollowUpCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    customer = (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none()
    if not customer:
        raise HTTPException(404, "客户不存在")
    fu = CustomerFollowUp(
        customer_id=customer.id,
        created_by=current_user.id,
        **body.model_dump(),
    )
    db.add(fu)
    await db.commit()
    await db.refresh(fu)
    return Resp.ok(FollowUpOut.model_validate(fu))
