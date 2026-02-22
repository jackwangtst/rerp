from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user, hash_password
from app.core.response import Resp, PageResp
from app.models.user import SysUser
from app.schemas.user import UserCreate, UserUpdate, UserOut

router = APIRouter(prefix="/users", tags=["用户管理"])

ADMIN_ONLY = "ROLE_ADMIN"


def require_admin(current_user: SysUser = Depends(get_current_user)):
    if current_user.role != ADMIN_ONLY:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


@router.get("", response_model=PageResp[UserOut])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(require_admin),
):
    offset = (page - 1) * page_size
    total = (await db.execute(select(func.count()).select_from(SysUser))).scalar()
    users = (await db.execute(select(SysUser).offset(offset).limit(page_size))).scalars().all()
    return PageResp(data=[UserOut.model_validate(u) for u in users], total=total, page=page, page_size=page_size)


@router.post("", response_model=Resp[UserOut])
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(require_admin),
):
    exists = (await db.execute(select(SysUser).where(SysUser.username == body.username))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = SysUser(
        username=body.username,
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        role=body.role,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return Resp.ok(UserOut.model_validate(user))


@router.put("/{user_id}", response_model=Resp[UserOut])
async def update_user(
    user_id: str,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(require_admin),
):
    user = (await db.execute(select(SysUser).where(SysUser.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        if field == "password":
            setattr(user, "password_hash", hash_password(value))
        else:
            setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return Resp.ok(UserOut.model_validate(user))


@router.delete("/{user_id}", response_model=Resp)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(require_admin),
):
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    user = (await db.execute(select(SysUser).where(SysUser.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    await db.delete(user)
    await db.commit()
    return Resp.ok(message="已删除")
