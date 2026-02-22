import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    full_name: str
    email: str | None
    phone: str | None
    role: str
    is_active: bool
    last_login: datetime | None
    created_at: datetime


class UserCreate(BaseModel):
    username: str
    full_name: str
    password: str
    role: str
    email: str | None = None
    phone: str | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    is_active: bool | None = None
    password: str | None = None
