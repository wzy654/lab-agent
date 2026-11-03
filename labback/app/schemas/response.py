#统一响应类
from typing import Any
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class Result(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T | None = None

    @classmethod
    def success(cls, data: T | None = None, message: str = "success"):
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, code: int = 400, message: str = "fail"):
        return cls(code=code, message=message, data=None)

class PageResult(BaseModel):
    """分页结果"""
    list: Any = []
    total: int = 0
