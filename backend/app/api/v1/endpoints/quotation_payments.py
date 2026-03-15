from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.response import Resp, PageResp
from app.models.user import SysUser
from app.models.quotation_payment import QuotationPayment, QuotationPaymentRecord

router = APIRouter(prefix="/quotation-payments", tags=["收款管理"])


class QuotationPaymentOut(BaseModel):
    id: str
    quotation_id: str
    quote_no: str
    customer_name: Optional[str]
    total_amount: float
    received_amount: float
    status: str
    received_date: Optional[date]
    payment_method: Optional[str]
    remark: Optional[str]

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj):
        return cls(
            id=str(obj.id),
            quotation_id=str(obj.quotation_id),
            quote_no=obj.quote_no,
            customer_name=obj.customer_name,
            total_amount=float(obj.total_amount),
            received_amount=float(obj.received_amount),
            status=obj.status,
            received_date=obj.received_date,
            payment_method=obj.payment_method,
            remark=obj.remark,
        )


class QuotationPaymentUpdate(BaseModel):
    remark: Optional[str] = None


class PaymentRecordCreate(BaseModel):
    amount: float
    received_date: date
    payment_method: str = "对公转账"
    remark: Optional[str] = None


class PaymentRecordOut(BaseModel):
    id: str
    payment_id: str
    amount: float
    received_date: date
    payment_method: str
    remark: Optional[str]
    created_at: datetime

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=str(obj.id),
            payment_id=str(obj.payment_id),
            amount=float(obj.amount),
            received_date=obj.received_date,
            payment_method=obj.payment_method,
            remark=obj.remark,
            created_at=obj.created_at,
        )


def _compute_status(received: Decimal, total: Decimal) -> str:
    if received <= 0:
        return "待收款"
    elif received >= total:
        return "已收款"
    return "部分收款"


@router.get("", response_model=PageResp[QuotationPaymentOut])
async def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    q = select(QuotationPayment)
    if status:
        q = q.where(QuotationPayment.status == status)
    if keyword:
        q = q.where(
            QuotationPayment.customer_name.ilike(f"%{keyword}%") |
            QuotationPayment.quote_no.ilike(f"%{keyword}%")
        )
    q = q.order_by(QuotationPayment.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResp(data=[QuotationPaymentOut.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)


@router.get("/{payment_id}/records", response_model=Resp[list[PaymentRecordOut]])
async def list_payment_records(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    rows = (await db.execute(
        select(QuotationPaymentRecord)
        .where(QuotationPaymentRecord.payment_id == payment_id)
        .order_by(QuotationPaymentRecord.received_date.desc())
    )).scalars().all()
    return Resp.ok([PaymentRecordOut.from_orm(r) for r in rows])


@router.post("/{payment_id}/records", response_model=Resp[PaymentRecordOut])
async def add_payment_record(
    payment_id: str,
    body: PaymentRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    header = (await db.execute(
        select(QuotationPayment).where(QuotationPayment.id == payment_id)
    )).scalar_one_or_none()
    if not header:
        raise HTTPException(404, "收款记录不存在")

    rec = QuotationPaymentRecord(
        payment_id=header.id,
        created_by=current_user.id,
        amount=Decimal(str(body.amount)),
        received_date=body.received_date,
        payment_method=body.payment_method,
        remark=body.remark,
    )
    db.add(rec)
    await db.flush()

    total_received = (await db.execute(
        select(func.coalesce(func.sum(QuotationPaymentRecord.amount), 0))
        .where(QuotationPaymentRecord.payment_id == header.id)
    )).scalar()
    header.received_amount = Decimal(str(total_received))
    header.status = _compute_status(header.received_amount, header.total_amount)

    await db.commit()
    await db.refresh(rec)
    return Resp.ok(PaymentRecordOut.from_orm(rec))


@router.delete("/{payment_id}/records/{record_id}", response_model=Resp)
async def delete_payment_record(
    payment_id: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    rec = (await db.execute(
        select(QuotationPaymentRecord)
        .where(QuotationPaymentRecord.id == record_id,
               QuotationPaymentRecord.payment_id == payment_id)
    )).scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "记录不存在")

    await db.delete(rec)
    await db.flush()

    header = (await db.execute(
        select(QuotationPayment).where(QuotationPayment.id == payment_id)
    )).scalar_one_or_none()
    total_received = (await db.execute(
        select(func.coalesce(func.sum(QuotationPaymentRecord.amount), 0))
        .where(QuotationPaymentRecord.payment_id == payment_id)
    )).scalar()
    header.received_amount = Decimal(str(total_received))
    header.status = _compute_status(header.received_amount, header.total_amount)

    await db.commit()
    return Resp.ok(message="已删除")


@router.put("/{payment_id}", response_model=Resp[QuotationPaymentOut])
async def update_payment(
    payment_id: str,
    body: QuotationPaymentUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    rec = (await db.execute(select(QuotationPayment).where(QuotationPayment.id == payment_id))).scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "记录不存在")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(rec, k, v)
    await db.commit()
    await db.refresh(rec)
    return Resp.ok(QuotationPaymentOut.model_validate(rec))


@router.delete("/{payment_id}", response_model=Resp)
async def delete_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    rec = (await db.execute(select(QuotationPayment).where(QuotationPayment.id == payment_id))).scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "记录不存在")
    await db.delete(rec)
    await db.commit()
    return Resp.ok(message="已删除")
