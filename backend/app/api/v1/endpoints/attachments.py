import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.core.response import Resp
from app.models.attachment import Attachment
from app.models.user import SysUser
from app.schemas.attachment import AttachmentOut

router = APIRouter(prefix="/attachments", tags=["附件管理"])

# 允许的文件类型
ALLOWED_MIME = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.get("", response_model=Resp[list[AttachmentOut]])
async def list_attachments(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    rows = (await db.execute(
        select(Attachment)
        .where(Attachment.entity_type == entity_type, Attachment.entity_id == entity_id)
        .order_by(Attachment.created_at.asc())
    )).scalars().all()
    return Resp.ok([AttachmentOut.model_validate(r) for r in rows])


@router.post("", response_model=Resp[AttachmentOut])
async def upload_attachment(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    # 校验文件类型
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(400, f"不支持的文件类型：{file.content_type}，允许：PDF、Word、Excel、图片")

    # 读取并校验大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"文件大小超过限制（最大 20 MB）")

    # 保存到磁盘：uploads/<entity_type>/<uuid><ext>
    upload_dir = Path(settings.UPLOAD_DIR) / entity_type
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix
    saved_name = f"{uuid.uuid4().hex}{ext}"
    saved_path = upload_dir / saved_name
    saved_path.write_bytes(content)

    file_url = f"/uploads/{entity_type}/{saved_name}"

    attachment = Attachment(
        entity_type=entity_type,
        entity_id=entity_id,
        file_name=file.filename,
        file_url=file_url,
        file_size=len(content),
        mime_type=file.content_type,
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return Resp.ok(AttachmentOut.model_validate(attachment))


@router.delete("/{attachment_id}", response_model=Resp)
async def delete_attachment(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
    _: SysUser = Depends(get_current_user),
):
    att = (await db.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )).scalar_one_or_none()
    if not att:
        raise HTTPException(404, "附件不存在")

    # 删除磁盘文件
    disk_path = Path(settings.UPLOAD_DIR) / att.file_url.lstrip("/uploads/")
    if disk_path.exists():
        disk_path.unlink()

    await db.delete(att)
    await db.commit()
    return Resp.ok(message="已删除")
