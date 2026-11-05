from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import BizError
from app.models.lab import Lab
from app.schemas.response import PageResult
from app.schemas.lab import LabResponse


def get_lab_page(
        db: Session = Depends(get_db),
        page: int = 1,
        page_size: int = 10,
        name: str | None = None,
):
    """获取实验室分页列表（可按名称模糊搜索）"""
    query = db.query(Lab)
    # name 参数有值才拼过滤条件，like %xx% 表示包含关键字的都算匹配
    if name:
        query = query.filter(Lab.name.like(f"%{name}%"))
    # 先查总数（分页控件需要），再查当前页的数据
    total = query.count()
    # order_by id 倒序：新增的实验室排在最前面
    # offset 跳过前几页的数据，limit 只取当前页的条数
    labs = query.order_by(Lab.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PageResult(
        list=[LabResponse.model_validate(lab) for lab in labs],
        total=total,
    )


def add_lab(db, data):
    """新增实验室"""
    # 实验室名称不允许重复：先查同名的是否存在
    lab = db.query(Lab).filter(Lab.name == data.name).first()
    if lab:
        raise BizError(message="实验室名称已存在")
    # 开放/关闭时间是「时:分」格式的字符串，这里校验关闭时间必须晚于开放时间
    if data.close_time <= data.open_time:
        raise BizError(message="关闭时间必须晚于开放时间")
    lab = Lab(
        name=data.name,
        capacity=data.capacity,
        open_time=data.open_time,
        close_time=data.close_time,
        description=data.description,
        location=data.location,
        img=data.img,
        status="1",  # 新增的实验室默认启用
    )
    db.add(lab)
    db.commit()
    db.refresh(lab)  # 刷新后拿到数据库生成的 id、创建时间等完整字段
    return LabResponse.model_validate(lab)


def update_lab(db, data):
    """管理员编辑实验室（按 id 定位）"""
    lab = db.get(Lab, data.id)
    if not lab:
        raise BizError(message="实验室不存在")
    # 如果要改名称，检查新名称是否和其他实验室重名（排除自己）
    if data.name is not None:
        exists = db.query(Lab).filter(Lab.name == data.name, Lab.id != data.id).first()
        if exists:
            raise BizError(message="实验室名称已存在")
    # 开放/关闭时间如果同时传了，校验先后关系
    if data.open_time and data.close_time and data.close_time <= data.open_time:
        raise BizError(message="关闭时间必须晚于开放时间")
    # 只更新显式传入的字段，id 是定位用的不参与更新
    dump = data.model_dump(exclude_unset=True, exclude={"id"})
    for field, value in dump.items():
        setattr(lab, field, value)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def set_status(db, data):
    """管理员启用/禁用实验室"""
    lab = db.get(Lab, data.id)
    if not lab:
        raise BizError(message="实验室不存在")
    # 状态值只允许 "0"禁用 / "1"启用（与数据库约定一致）
    if data.status not in ("0", "1"):
        raise BizError(message="状态不合法，只支持 0(禁用) 或 1(启用)")
    lab.status = data.status
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def delete_lab(db, lab_id: int):
    """管理员删除实验室（按路径参数里的 id 定位）"""
    lab = db.get(Lab, lab_id)
    if not lab:
        raise BizError(message="实验室不存在")
    db.delete(lab)
    db.commit()
