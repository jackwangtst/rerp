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
from app.models.invoice import Invoice
from app.models.quotation_payment import QuotationPayment

router = APIRouter(prefix="/invoices", tags=["发票管理"])

INVOICE_TYPES = ["增值税普通发票", "增值税专用发票"]
INVOICE_STATUSES = ["待开具", "已开具", "已邮寄", "已上传"]


class InvoiceCreate(BaseModel):
    payment_id: Optional[str] = None
    customer_name: str
    quote_no: Optional[str] = None
    invoice_type: str = "增值税普通发票"
    invoice_title: str
    tax_no: Optional[str] = None
    invoice_amount: float
    invoice_no: Optional[str] = None
    issue_date: Optional[date] = None
    status: str = "待开具"
    remark: Optional[str] = None


class InvoiceUpdate(BaseModel):
    invoice_type: Optional[str] = None
    invoice_title: Optional[str] = None
    tax_no: Optional[str] = None
    invoice_amount: Optional[float] = None
    invoice_no: Optional[str] = None
    issue_date: Optional[date] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class InvoiceOut(BaseModel):
    id: str
    payment_id: Optional[str]
    customer_name: str
    quote_no: Optional[str]
    invoice_type: str
    invoice_title: str
    tax_no: Optional[str]
    invoice_amount: float
    invoice_no: Optional[str]
    issue_date: Optional[date]
    status: str
    remark: Optional[str]
    created_at: datetime

    @classmethod
    def from_orm(cls, obj: Invoice) -> "InvoiceOut":
        return cls(
            id=str(obj.id),
            payment_id=str(obj.payment_id) if obj.payment_id else None,
            customer_name=obj.customer_name,
            quote_no=obj.quote_no,
            invoice_type=obj.invoice_type,
            invoice_title=obj.invoice_title,
            tax_no=obj.tax_no,
            invoice_amount=float(obj.invoice_amount),
            invoice_no=obj.invoice_no,
            issue_date=obj.issue_date,
            status=obj.status,
            remark=obj.remark,
            created_at=obj.created_at,
        )


@router.get("", response_model=PageResp[InvoiceOut])
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    q = select(Invoice)
    if status:
        q = q.where(Invoice.status == status)
    if keyword:
        q = q.where(
            Invoice.customer_name.ilike(f"%{keyword}%") |
            Invoice.quote_no.ilike(f"%{keyword}%") |
            Invoice.invoice_no.ilike(f"%{keyword}%")
        )
    q = q.order_by(Invoice.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResp(data=[InvoiceOut.from_orm(r) for r in rows], total=total, page=page, page_size=page_size)


@router.post("", response_model=Resp[InvoiceOut])
async def create_invoice(
    body: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    # 如果关联了收款记录，自动填充 customer_name / quote_no
    payment_uuid = None
    if body.payment_id:
        from uuid import UUID as _UUID
        try:
            payment_uuid = _UUID(body.payment_id)
        except ValueError:
            raise HTTPException(400, "payment_id 格式错误")
        payment = (await db.execute(
            select(QuotationPayment).where(QuotationPayment.id == payment_uuid)
        )).scalar_one_or_none()
        if not payment:
            raise HTTPException(404, "收款记录不存在")

    inv = Invoice(
        payment_id=payment_uuid,
        customer_name=body.customer_name,
        quote_no=body.quote_no,
        invoice_type=body.invoice_type,
        invoice_title=body.invoice_title,
        tax_no=body.tax_no,
        invoice_amount=Decimal(str(body.invoice_amount)),
        invoice_no=body.invoice_no,
        issue_date=body.issue_date,
        status=body.status,
        remark=body.remark,
        created_by=current_user.id,
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    return Resp.ok(InvoiceOut.from_orm(inv))


@router.put("/{invoice_id}", response_model=Resp[InvoiceOut])
async def update_invoice(
    invoice_id: str,
    body: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    inv = (await db.execute(select(Invoice).where(Invoice.id == invoice_id))).scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "发票不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        if k == "invoice_amount" and v is not None:
            v = Decimal(str(v))
        setattr(inv, k, v)
    await db.commit()
    await db.refresh(inv)
    return Resp.ok(InvoiceOut.from_orm(inv))


@router.delete("/{invoice_id}", response_model=Resp)
async def delete_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    inv = (await db.execute(select(Invoice).where(Invoice.id == invoice_id))).scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "发票不存在")
    await db.delete(inv)
    await db.commit()
    return Resp.ok(message="已删除")
