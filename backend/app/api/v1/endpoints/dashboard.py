from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.lead import Lead
from app.models.customer import Customer
from app.models.contract import Contract
from app.models.quotation_payment import QuotationPayment
from app.models.project import ProjectTask

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    today = date.today()

    # 本月新增线索
    leads_count = await db.scalar(
        select(func.count()).select_from(Lead).where(
            extract("year", Lead.created_at) == today.year,
            extract("month", Lead.created_at) == today.month,
        )
    )

    # 在服务客户数（状态为"服务中"）
    customers_count = await db.scalar(
        select(func.count()).select_from(Customer).where(Customer.status == "服务中")
    )

    # 本月新签合同数（本月创建的已接受报价单）
    from app.models.quotation import Quotation
    contracts_count = await db.scalar(
        select(func.count()).select_from(Quotation).where(
            extract("year", Quotation.created_at) == today.year,
            extract("month", Quotation.created_at) == today.month,
            Quotation.status == "已接受",
        )
    )

    # 待执行任务数（状态为"待开始"或"进行中"）
    tasks_count = await db.scalar(
        select(func.count()).select_from(ProjectTask).where(
            ProjectTask.status.in_(["待开始", "进行中"])
        )
    )

    # 未收款金额 = quotation_payment 中 total_amount - received_amount 之和（非已收款）
    total_amount = await db.scalar(
        select(func.coalesce(func.sum(QuotationPayment.total_amount), 0)).where(
            QuotationPayment.status != "已收款"
        )
    )
    received_amount = await db.scalar(
        select(func.coalesce(func.sum(QuotationPayment.received_amount), 0)).where(
            QuotationPayment.status != "已收款"
        )
    )
    unpaid_amount = float(total_amount or 0) - float(received_amount or 0)

    return {
        "monthly_leads": leads_count or 0,
        "active_customers": customers_count or 0,
        "monthly_contracts": contracts_count or 0,
        "pending_tasks": tasks_count or 0,
        "unpaid_amount": round(unpaid_amount, 2),
    }
