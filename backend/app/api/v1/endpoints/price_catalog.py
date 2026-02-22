from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.response import Resp, PageResp
from app.models.user import SysUser
from app.models.price_catalog import PriceCatalog
from app.schemas.price_catalog import (
    PriceCatalogCreate, PriceCatalogUpdate,
    PriceCatalogOut, PriceCatalogSearchItem,
)

router = APIRouter(prefix="/price-catalog", tags=["价格库"])


@router.get("/countries", response_model=Resp[list[str]])
async def list_countries(
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    """返回价格库中所有不重复的国家列表（已排序）"""
    rows = (await db.execute(
        select(distinct(PriceCatalog.country))
        .where(PriceCatalog.country.isnot(None))
        .order_by(PriceCatalog.country)
    )).scalars().all()
    return Resp.ok(list(rows))


@router.get("/search", response_model=Resp[list[PriceCatalogSearchItem]])
async def search_price_catalog(
    keyword: str = Query("", min_length=0),
    country: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    """报价明细搜索用，按国家+关键字过滤（最多50条）"""
    q = select(PriceCatalog)
    if country:
        q = q.where(PriceCatalog.country == country)
    if keyword:
        kw = f"%{keyword}%"
        q = q.where(PriceCatalog.name.ilike(kw))
    q = q.order_by(PriceCatalog.country, PriceCatalog.name).limit(50)
    rows = (await db.execute(q)).scalars().all()
    return Resp.ok([PriceCatalogSearchItem.model_validate(r) for r in rows])


@router.get("", response_model=PageResp[PriceCatalogOut])
async def list_price_catalog(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    q = select(PriceCatalog)
    if keyword:
        kw = f"%{keyword}%"
        q = q.where(or_(
            PriceCatalog.name.ilike(kw),
            PriceCatalog.country.ilike(kw),
        ))
    q = q.order_by(PriceCatalog.country, PriceCatalog.name)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PageResp(data=[PriceCatalogOut.model_validate(r) for r in rows], total=total, page=page, page_size=page_size)


@router.post("", response_model=Resp[PriceCatalogOut])
async def create_price_catalog(
    body: PriceCatalogCreate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    item = PriceCatalog(**body.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return Resp.ok(PriceCatalogOut.model_validate(item))


@router.put("/{item_id}", response_model=Resp[PriceCatalogOut])
async def update_price_catalog(
    item_id: str,
    body: PriceCatalogUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    item = (await db.execute(select(PriceCatalog).where(PriceCatalog.id == item_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(404, "记录不存在")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return Resp.ok(PriceCatalogOut.model_validate(item))


@router.delete("/{item_id}", response_model=Resp)
async def delete_price_catalog(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    item = (await db.execute(select(PriceCatalog).where(PriceCatalog.id == item_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(404, "记录不存在")
    await db.delete(item)
    await db.commit()
    return Resp.ok(message="已删除")
