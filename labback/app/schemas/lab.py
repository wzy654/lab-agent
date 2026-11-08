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
    status: int
    # from_attributes：允许直接从 SQLAlchemy 模型对象读取同名字段转换
    model_config = ConfigDict(from_attributes=True)


class LabEquipmentItem(BaseModel):
    """实验室详情里嵌套的设备信息（精简版，只放浏览时关心的字段）"""
    id: int
    name: str
    spec: str | None
    quantity: int
    description: str | None
    img: str | None
    status: int
    # from_attributes：字段名与 Equipment 模型一致，可直接从模型对象转换
    model_config = ConfigDict(from_attributes=True)


class LabDetailResponse(LabResponse):
    """实验室详情响应：在基础信息之上，附带该实验室挂载的设备列表"""
    # 继承 LabResponse 的全部字段，额外加一个设备列表，默认空列表
    equipment: list[LabEquipmentItem] = []


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
    status: int  # 0 禁用 1 启用
