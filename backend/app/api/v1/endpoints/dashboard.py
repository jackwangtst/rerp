from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.lead import Lead
from app.models.customer import Customer
from app.models.contract import Contract, PaymentRecord
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

    # 本月新签合同数（本月创建，排除已终止）
    contracts_count = await db.scalar(
        select(func.count()).select_from(Contract).where(
            extract("year", Contract.created_at) == today.year,
            extract("month", Contract.created_at) == today.month,
            Contract.status != "已终止",
        )
    )

    # 待执行任务数（状态为"待开始"或"进行中"）
    tasks_count = await db.scalar(
        select(func.count()).select_from(ProjectTask).where(
            ProjectTask.status.in_(["待开始", "进行中"])
        )
    )

    # 未收款金额 = 合同总额合计 - 已收款合计（排除已终止合同）
    total_contract_amount = await db.scalar(
        select(func.coalesce(func.sum(Contract.total_amount), 0)).where(
            Contract.status != "已终止"
        )
    )
    total_received_amount = await db.scalar(
        select(func.coalesce(func.sum(PaymentRecord.received_amount), 0)).join(
            Contract, PaymentRecord.contract_id == Contract.id
        ).where(Contract.status != "已终止")
    )
    unpaid_amount = float(total_contract_amount or 0) - float(total_received_amount or 0)

    return {
        "monthly_leads": leads_count or 0,
        "active_customers": customers_count or 0,
        "monthly_contracts": contracts_count or 0,
        "pending_tasks": tasks_count or 0,
        "unpaid_amount": round(unpaid_amount, 2),
    }
