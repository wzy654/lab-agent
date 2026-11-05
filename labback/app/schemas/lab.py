from pydantic import BaseModel, ConfigDict


class LabResponse(BaseModel):
    """实验室响应（列表、新增/编辑后的返回值都用它）"""
    id: int
    name: str
    description: str | None
    location: str | None
    capacity: int
    open_time: str
    close_time: str
    img: str | None
    status: str
    # from_attributes：允许直接从 SQLAlchemy 模型对象读取同名字段转换
    model_config = ConfigDict(from_attributes=True)


class LabAddRequest(BaseModel):
    """管理员新增实验室请求"""
    name: str
    # 容量、开放/关闭时间在数据库里是非空字段，所以新增时必传
    capacity: int
    open_time: str
    close_time: str
    # 以下字段数据库允许为空，新增时可不传
    description: str | None = None
    location: str | None = None
    # 图片路径：由前端先调 /files/upload 拿到相对路径再传进来
    img: str | None = None


class LabUpdateRequest(BaseModel):
    """管理员编辑实验室请求（按 id 定位，只更新显式传入的字段）"""
    id: int
    # 以下全部可选：没传的字段保持数据库原值
    name: str | None = None
    description: str | None = None
    location: str | None = None
    capacity: int | None = None
    open_time: str | None = None
    close_time: str | None = None
    img: str | None = None


class LabSetStatusRequest(BaseModel):
    """管理员启用/禁用实验室请求"""
    id: int
    status: str  # "0"禁用 "1"启用
