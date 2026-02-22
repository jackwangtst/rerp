from __future__ import annotations
from decimal import Decimal

from sqlalchemy import Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class PriceCatalog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "price_catalog"

    country: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cert_type: Mapped[str | None] = mapped_column(String(50))            # 强制性/自愿性
    sample_qty: Mapped[int | None] = mapped_column(SmallInteger)         # 样机数量
    based_on_report: Mapped[str | None] = mapped_column(String(10))      # 基于CE/FCC报告转证 Y/N
    lead_weeks: Mapped[int | None] = mapped_column(SmallInteger)         # 认证周期（周）
    includes_testing: Mapped[str | None] = mapped_column(String(10))     # 包含测试+转证 Y/N
    cert_validity_years: Mapped[int | None] = mapped_column(SmallInteger)# 证书有效期（年）
    series_apply: Mapped[str | None] = mapped_column(String(10))         # 可系列申请 Y/N
    ref_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))    # 预估总体费用
    remark: Mapped[str | None] = mapped_column(Text)
