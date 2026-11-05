from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.User import User
from app.schemas.equipment import (EquipmentAddRequest,
                                   EquipmentSetStatusRequest,
                                   EquipmentUpdateRequest)
from app.schemas.response import Result
from app.services import equipment_service

equipment_router = APIRouter(prefix="/equipment", tags=["设备管理"])


@equipment_router.get("/list")
def get_equipment_list(page: int = 1,
                       page_size: int = 10,
                       name: str | None = None,
                       lab_id: int | None = None,
                       current_admin: User = Depends(get_current_admin),
                       db: Session = Depends(get_db)):
    """获取设备分页列表（需管理员，可按名称搜索、按实验室过滤）"""
    return Result.success(equipment_service.get_equipment_page(db, page, page_size, name, lab_id),
                          message="获取设备列表成功")


@equipment_router.post("/add")
def add_equipment(data: EquipmentAddRequest,
                  current_admin: User = Depends(get_current_admin),
                  db: Session = Depends(get_db)):
    """管理员新增设备"""
    return Result.success(equipment_service.add_equipment(db, data), message="新增设备成功")


@equipment_router.put("/admin/update")
def update_equipment(data: EquipmentUpdateRequest,
                     current_admin: User = Depends(get_current_admin),
                     db: Session = Depends(get_db)):
    """管理员编辑设备（按 id 定位）"""
    return Result.success(equipment_service.update_equipment(db, data), message="设备更新成功")


@equipment_router.put("/admin/status")
def set_equipment_status(data: EquipmentSetStatusRequest,
                         current_admin: User = Depends(get_current_admin),
                         db: Session = Depends(get_db)):
    """管理员启用/禁用设备（按 id 定位）"""
    return Result.success(equipment_service.set_status(db, data), message="状态设置成功")


@equipment_router.delete("/{equipment_id}")
def delete_equipment(equipment_id: int,
                     current_admin: User = Depends(get_current_admin),
                     db: Session = Depends(get_db)):
    """管理员删除设备（路径参数传 id，如 DELETE /api/equipment/3）"""
    equipment_service.delete_equipment(db, equipment_id)
    return Result.success(message="删除设备成功")
