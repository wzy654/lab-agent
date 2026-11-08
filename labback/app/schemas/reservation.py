from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReservationCreateRequest(BaseModel):
    """创建预约请求：日期与时间均为字符串，格式 YYYY-MM-DD / HH:mm"""
    lab_id: int
    # 可空：不传 = 预约整个实验室；传 = 预约实验室里的某台设备
    equipment_id: int | None = None
    date: str      # "YYYY-MM-DD"
    start_time: str  # "HH:mm"
    end_time: str    # "HH:mm"
    remark: str | None = None


class ReservationResponse(BaseModel):
    """预约记录响应（我的预约列表、管理员审核列表都用它）

    user_name / lab_name / equipment_name 由 service 层通过 relationship
    取关联对象补齐（模型对象上没有这几个属性，所以给默认值再赋值）。
    """
    id: int
    user_id: int
    user_name: str = ""            # 预约人姓名（管理员审核列表要显示）
    lab_id: int
    lab_name: str = ""             # 实验室名称
    equipment_id: int | None = None
    equipment_name: str | None = None  # 设备名（预约整间实验室时为 null）
    date: str
    start_time: str
    end_time: str
    remark: str | None = None
    status: int                    # 0 待审核 / 1 已通过 / 2 已拒绝 / 3 已取消
    create_time: datetime | None = None  # 提交时间
    # from_attributes：允许直接从 SQLAlchemy 模型对象读取同名字段转换
    model_config = ConfigDict(from_attributes=True)


class ReservationCancelRequest(BaseModel):
    """用户取消自己的预约请求（按 id 定位）"""
    id: int


class ReservationReviewRequest(BaseModel):
    """管理员审核预约请求：status 只允许 1(通过) 或 2(拒绝)"""
    id: int
    status: int