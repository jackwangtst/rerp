from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class Resp(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: T | None = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "ok") -> "Resp":
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, message: str, code: int = 400) -> "Resp":
        return cls(code=code, message=message)


class PageResp(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
