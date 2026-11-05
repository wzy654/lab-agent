from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.User import User
from app.schemas.lab import (LabAddRequest, LabSetStatusRequest,
                             LabUpdateRequest)
from app.schemas.response import Result
from app.services import lab_service

lab_router = APIRouter(prefix="/lab", tags=["实验室管理"])


@lab_router.get("/list")
def get_lab_list(page: int = 1,
                 page_size: int = 10,
                 name: str | None = None,
                 current_admin: User = Depends(get_current_admin),
                 db: Session = Depends(get_db)):
    """获取实验室分页列表（需管理员）"""
    return Result.success(lab_service.get_lab_page(db, page, page_size, name),
                          message="获取实验室列表成功")


@lab_router.post("/add")
def add_lab(data: LabAddRequest,
            current_admin: User = Depends(get_current_admin),
            db: Session = Depends(get_db)):
    """管理员新增实验室"""
    return Result.success(lab_service.add_lab(db, data), message="新增实验室成功")


@lab_router.put("/admin/update")
def update_lab(data: LabUpdateRequest,
               current_admin: User = Depends(get_current_admin),
               db: Session = Depends(get_db)):
    """管理员编辑实验室（按 id 定位）"""
    return Result.success(lab_service.update_lab(db, data), message="实验室更新成功")


@lab_router.put("/admin/status")
def set_lab_status(data: LabSetStatusRequest,
                   current_admin: User = Depends(get_current_admin),
                   db: Session = Depends(get_db)):
    """管理员启用/禁用实验室（按 id 定位）"""
    return Result.success(lab_service.set_status(db, data), message="状态设置成功")


@lab_router.delete("/{lab_id}")
def delete_lab(lab_id: int,
               current_admin: User = Depends(get_current_admin),
               db: Session = Depends(get_db)):
    """管理员删除实验室（路径参数传 id，如 DELETE /api/lab/3）"""
    lab_service.delete_lab(db, lab_id)
    return Result.success(message="删除实验室成功")
