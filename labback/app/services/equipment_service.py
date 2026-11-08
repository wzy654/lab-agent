from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import BizError
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.schemas.response import PageResult
from app.schemas.equipment import EquipmentResponse


def _to_response(eq: Equipment) -> EquipmentResponse:
    """把设备模型对象转成响应模型，并补充所属实验室的名称"""
    # 第一步：按 from_attributes 读取设备的同名字段（此时 lab_name 还是空值）
    response = EquipmentResponse.model_validate(eq)
    # 第二步：从关联的实验室对象（eq.lab 触发懒加载查库）取名称补充进去
    # 注：不用 model_validate(eq, update=...) 是因为旧版 Pydantic 不支持 update 参数
    response.lab_name = eq.lab.name
    return response


def get_equipment_page(
        db: Session = Depends(get_db),
        page: int = 1,
        page_size: int = 10,
        name: str | None = None,
        lab_id: int | None = None,
):
    """获取设备分页列表（可按名称模糊搜索、按所属实验室过滤）"""
    query = db.query(Equipment)
    # name 参数有值才拼过滤条件，like %xx% 表示包含关键字的都算匹配
    if name:
        query = query.filter(Equipment.name.like(f"%{name}%"))
    # lab_id 参数有值就只查该实验室下的设备
    if lab_id:
        query = query.filter(Equipment.lab_id == lab_id)
    # 先查总数（分页控件需要），再查当前页的数据；id 倒序让新增的排在最前面
    total = query.count()
    equipments = query.order_by(Equipment.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PageResult(
        list=[_to_response(eq) for eq in equipments],
        total=total,
    )


def _check_capacity(db, lab, quantity: int, exclude_id: int | None = None):
    """校验设备数量总和不超过实验室容量

    lab: 目标实验室（新增时为选定的实验室，编辑时可能是换过去的实验室）
    quantity: 本次要放入该实验室的设备数量
    exclude_id: 编辑时排除自己（自己原来的数量不重复计算）
    """
    # 统计该实验室下已有设备的数量总和
    query = db.query(Equipment).filter(Equipment.lab_id == lab.id)
    if exclude_id is not None:
        query = query.filter(Equipment.id != exclude_id)
    used = sum(eq.quantity for eq in query.all())
    # 加上本次的数量后不能超过实验室容量
    if used + quantity > lab.capacity:
        raise BizError(
            message=f"实验室「{lab.name}」容量不足：已有设备 {used} 台，"
                    f"再放入 {quantity} 台将超过容量 {lab.capacity}"
        )


def add_equipment(db, data):
    """新增设备"""
    # 设备必须挂在某个实验室下：先确认实验室存在，否则给出友好报错
    lab = db.get(Lab, data.lab_id)
    if not lab:
        raise BizError(message="所属实验室不存在")
    # 校验设备数量是否超过实验室容量
    _check_capacity(db, lab, data.quantity)
    eq = Equipment(
        lab_id=data.lab_id,
        name=data.name,
        quantity=data.quantity,
        spec=data.spec,
        description=data.description,
        img=data.img,
        status=1,  # 新增的设备默认启用
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)  # 刷新后拿到数据库生成的 id 等完整字段
    return _to_response(eq)


def update_equipment(db, data):
    """管理员编辑设备（按 id 定位）"""
    eq = db.get(Equipment, data.id)
    if not eq:
        raise BizError(message="设备不存在")
    # 如果要换所属实验室，校验新实验室是否存在
    if data.lab_id is not None:
        lab = db.get(Lab, data.lab_id)
        if not lab:
            raise BizError(message="所属实验室不存在")
    # 容量校验：改了数量、或换了实验室，都需要重新检查不超容量
    # 目标实验室：换了就用新实验室，没换就是原来的
    if data.quantity is not None or data.lab_id is not None:
        target_lab = db.get(Lab, data.lab_id) if data.lab_id is not None else eq.lab
        # 新数量：改了就用新值，没改就是原来的
        new_quantity = data.quantity if data.quantity is not None else eq.quantity
        # exclude_id 排除自己，避免把自己的旧数量重复算进「已有设备」
        _check_capacity(db, target_lab, new_quantity, exclude_id=eq.id)
    # 只更新显式传入的字段，id 是定位用的不参与更新
    dump = data.model_dump(exclude_unset=True, exclude={"id"})
    for field, value in dump.items():
        setattr(eq, field, value)
    db.commit()
    db.refresh(eq)
    return _to_response(eq)


def set_status(db, data):
    """管理员启用/禁用设备"""
    eq = db.get(Equipment, data.id)
    if not eq:
        raise BizError(message="设备不存在")
    # 状态值只允许 0 禁用 / 1 启用（与数据库约定一致）
    if data.status not in (0, 1):
        raise BizError(message="状态不合法，只支持 0(禁用) 或 1(启用)")
    eq.status = data.status
    db.commit()
    db.refresh(eq)
    return _to_response(eq)


def delete_equipment(db, equipment_id: int):
    """管理员删除设备（按路径参数里的 id 定位）"""
    eq = db.get(Equipment, equipment_id)
    if not eq:
        raise BizError(message="设备不存在")
    db.delete(eq)
    db.commit()
