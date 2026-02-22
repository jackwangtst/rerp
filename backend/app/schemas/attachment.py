import uuid
from datetime import datetime
from pydantic import BaseModel


class AttachmentOut(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    file_name: str
    file_url: str
    file_size: int | None
    mime_type: str | None
    uploaded_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
