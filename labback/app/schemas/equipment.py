# 设备模块的数据契约（与前端 types.ts 的 DeviceInfo 保持一致）
from pydantic import BaseModel, ConfigDict, Field


class EquipmentResponse(BaseModel):
    """设备响应（列表、新增/编辑后的返回值都用它）"""
    id: int
    lab_id: int
    # 所属实验室的名称：不在 equipment 表里，service 层转换后补充
    # 给默认值 ""：model_validate 读取设备对象时该属性不存在，有默认值才不会报缺字段
    lab_name: str = ""
    name: str
    description: str | None
    quantity: int
    spec: str | None
    img: str | None
    status: str
    # from_attributes：允许直接从 SQLAlchemy 模型对象读取同名字段转换
    model_config = ConfigDict(from_attributes=True)


class EquipmentAddRequest(BaseModel):
    """管理员新增设备请求"""
    # 所属实验室：必填，后端会校验该实验室是否存在
    lab_id: int
    name: str
    # 数量默认 1 台，最少 1（ge=1 表示大于等于 1，不满足直接返回参数错误）
    quantity: int = Field(default=1, ge=1)
    # 以下字段数据库允许为空，新增时可不传
    spec: str | None = None
    description: str | None = None
    # 图片路径：由前端先调 /files/upload 拿到相对路径再传进来
    img: str | None = None


class EquipmentUpdateRequest(BaseModel):
    """管理员编辑设备请求（按 id 定位，只更新显式传入的字段）"""
    id: int
    # 以下全部可选：没传的字段保持数据库原值
    lab_id: int | None = None
    name: str | None = None
    description: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    spec: str | None = None
    img: str | None = None


class EquipmentSetStatusRequest(BaseModel):
    """管理员启用/禁用设备请求"""
    id: int
    status: str  # "0"禁用 "1"启用
