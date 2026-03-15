from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.response import Resp, PageResp
from app.models.user import SysUser
from app.models.quotation import Quotation
from app.models.quotation_payment import QuotationPayment
from app.models.opportunity import Opportunity
from app.models.customer import Customer
from app.schemas.quotation import (
    QuotationCreate, QuotationUpdate, QuotationOut, QuotationListItem,
)

router = APIRouter(prefix="/quotations", tags=["报价管理"])


def _next_quote_no(seq_val: int, year: int) -> str:
    return f"QT-{year}-{seq_val:04d}"


def _serialize_items(items):
    """将 items 中的 Decimal 转为 float 以便存入 JSONB"""
    result = []
    for item in items:
        d = item if isinstance(item, dict) else item.model_dump()
        for k in ("unit_price", "discount", "amount", "audit_days"):
            if d.get(k) is not None:
                d[k] = float(d[k])
        result.append(d)
    return result


# ── 报价列表 ─────────────────────────────────────────────────
@router.get("", response_model=PageResp[QuotationListItem])
async def list_quotations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    status: str | None = None,
    opp_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    q = select(Quotation)
    if status:
        q = q.where(Quotation.status == status)
    if opp_id:
        q = q.where(Quotation.opp_id == opp_id)
    q = q.order_by(Quotation.created_at.desc())

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResp(data=[QuotationListItem.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)


# ── 创建报价 ─────────────────────────────────────────────────
@router.post("", response_model=Resp[QuotationOut])
async def create_quotation(
    body: QuotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    from datetime import datetime
    year = datetime.now().year
    seq = (await db.execute(select(func.nextval("seq_quotation_no")))).scalar()

    data = body.model_dump(exclude={"items"})
    quotation = Quotation(
        quote_no=_next_quote_no(seq, year),
        created_by=current_user.id,
        items=_serialize_items(body.items),
        **data,
    )
    db.add(quotation)
    await db.flush()

    # 新建时若状态直接为"已接受"，自动创建收款记录
    if quotation.status == "已接受":
        cname = None
        if quotation.customer_id:
            cust = (await db.execute(
                select(Customer).where(Customer.id == quotation.customer_id)
            )).scalar_one_or_none()
            cname = cust.company_name if cust else None
        elif quotation.opp_id:
            opp = (await db.execute(
                select(Opportunity).where(Opportunity.id == quotation.opp_id)
            )).scalar_one_or_none()
            if opp and opp.customer_id:
                cust = (await db.execute(
                    select(Customer).where(Customer.id == opp.customer_id)
                )).scalar_one_or_none()
                cname = cust.company_name if cust else None
        db.add(QuotationPayment(
            quotation_id=quotation.id,
            customer_id=quotation.customer_id,
            quote_no=quotation.quote_no,
            customer_name=cname,
            total_amount=quotation.total_amount,
        ))

    await db.commit()
    await db.refresh(quotation)
    return Resp.ok(QuotationOut.model_validate(quotation))


# ── 报价详情 ─────────────────────────────────────────────────
@router.get("/{quot_id}", response_model=Resp[QuotationOut])
async def get_quotation(
    quot_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    quot = (await db.execute(select(Quotation).where(Quotation.id == quot_id))).scalar_one_or_none()
    if not quot:
        raise HTTPException(404, "报价单不存在")
    return Resp.ok(QuotationOut.model_validate(quot))


# ── 更新报价 ─────────────────────────────────────────────────
@router.put("/{quot_id}", response_model=Resp[QuotationOut])
async def update_quotation(
    quot_id: str,
    body: QuotationUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    quot = (await db.execute(select(Quotation).where(Quotation.id == quot_id))).scalar_one_or_none()
    if not quot:
        raise HTTPException(404, "报价单不存在")
    old_status = quot.status
    data = body.model_dump(exclude_unset=True)
    if "items" in data:
        data["items"] = _serialize_items(data["items"])
    for field, value in data.items():
        setattr(quot, field, value)

    # 状态变为"已接受"时，自动创建收款记录（若尚未创建）
    new_status = data.get("status", old_status)
    if new_status == "已接受" and old_status != "已接受":
        existing = (await db.execute(
            select(QuotationPayment).where(QuotationPayment.quotation_id == quot.id)
        )).scalar_one_or_none()
        if not existing:
            # 获取客户名称
            cname = None
            if quot.customer_id:
                cust = (await db.execute(
                    select(Customer).where(Customer.id == quot.customer_id)
                )).scalar_one_or_none()
                cname = cust.company_name if cust else None
            elif quot.opp_id:
                opp = (await db.execute(
                    select(Opportunity).where(Opportunity.id == quot.opp_id)
                )).scalar_one_or_none()
                if opp and opp.customer_id:
                    cust = (await db.execute(
                        select(Customer).where(Customer.id == opp.customer_id)
                    )).scalar_one_or_none()
                    cname = cust.company_name if cust else None
            db.add(QuotationPayment(
                quotation_id=quot.id,
                customer_id=quot.customer_id,
                quote_no=quot.quote_no,
                customer_name=cname,
                total_amount=quot.total_amount,
            ))

    await db.commit()
    await db.refresh(quot)
    return Resp.ok(QuotationOut.model_validate(quot))


# ── 删除报价 ─────────────────────────────────────────────────
@router.delete("/{quot_id}", response_model=Resp)
async def delete_quotation(
    quot_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    quot = (await db.execute(select(Quotation).where(Quotation.id == quot_id))).scalar_one_or_none()
    if not quot:
        raise HTTPException(404, "报价单不存在")
    await db.delete(quot)
    await db.commit()
    return Resp.ok(message="已删除")


# ── 导出 PDF ─────────────────────────────────────────────────
@router.get("/{quot_id}/pdf")
async def export_pdf(
    quot_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    quot = (await db.execute(
        select(Quotation).where(Quotation.id == quot_id)
    )).scalar_one_or_none()
    if not quot:
        raise HTTPException(404, "报价单不存在")

    # 获取关联的商机和客户名称
    customer_name = ""
    if quot.customer_id:
        customer = (await db.execute(
            select(Customer).where(Customer.id == quot.customer_id)
        )).scalar_one_or_none()
        customer_name = customer.company_name if customer else ""
    elif quot.opp_id:
        opp = (await db.execute(
            select(Opportunity).where(Opportunity.id == quot.opp_id)
        )).scalar_one_or_none()
        if opp:
            customer = (await db.execute(
                select(Customer).where(Customer.id == opp.customer_id)
            )).scalar_one_or_none()
            customer_name = customer.company_name if customer else (opp.opp_name or "")

    # 获取创建人姓名
    sales_person = ""
    if quot.created_by:
        creator = (await db.execute(
            select(SysUser).where(SysUser.id == quot.created_by)
        )).scalar_one_or_none()
        sales_person = creator.full_name if creator else ""

    from app.core.pdf import generate_quotation_pdf
    from decimal import Decimal

    pdf_bytes = generate_quotation_pdf(
        quote_no=quot.quote_no,
        created_at=quot.created_at.date(),
        valid_until=quot.valid_until,
        customer_name=customer_name,
        contact_name=quot.contact_name,
        contact_phone=quot.contact_phone,
        deliver_to_address=quot.deliver_to_address,
        product_name=quot.product_name,
        product_model=quot.product_model,
        sales_person=sales_person,
        items=quot.items or [],
        total_amount=quot.total_amount,
        discount_amount=quot.discount_amount,
        payment_terms=quot.payment_terms,
        remark=quot.remark,
    )

    filename = f"{quot.quote_no}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
