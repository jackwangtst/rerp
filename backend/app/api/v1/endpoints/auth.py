from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user
from app.core.response import Resp
from app.models.user import SysUser
from app.schemas.auth import TokenOut

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=Resp[TokenOut])
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SysUser).where(SysUser.username == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已禁用")

    await db.execute(
        update(SysUser)
        .where(SysUser.id == user.id)
        .values(last_login=datetime.now(timezone.utc))
    )
    await db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return Resp.ok(TokenOut(access_token=token, token_type="bearer"))


@router.get("/me", response_model=Resp)
async def me(current_user: SysUser = Depends(get_current_user)):
    return Resp.ok({
        "id": str(current_user.id),
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
    })
