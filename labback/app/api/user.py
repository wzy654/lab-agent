from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, get_current_admin
from app.models.User import User
from app.schemas.response import Result
from app.schemas.user import (AddUserRequest, AdminSetStatusRequest,
                              AdminUpdateUserRequest, PasswordUpdateRequest,
                              UserUpdateRequest)
from app.services import user_service

user_router = APIRouter(prefix="/user",tags=["用户信息"])

@user_router.get("/info")
def get_user_info(user: User = Depends(get_current_user)):
    """获取登录用户信息"""
    return Result.success(user_service.get_user_info(user), message="获取用户信息成功")

@user_router.put("/update")
def update_user_info(data: UserUpdateRequest,user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """更新登录用户信息"""
    return Result.success(user_service.update_user_info(db,user,data), message="更新用户信息成功")

@user_router.put("/password")
def update_password(data: PasswordUpdateRequest,user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """更新登录用户密码"""
    user_service.update_password(db, user, data)
    return Result.success()

@user_router.get("/list")
def get_user_list(page: int = 1,
                  page_size: int = 10,
                  username:str|None=None,
                  current_admin: User = Depends(get_current_admin),
                  db: Session = Depends(get_db)):
    """获取用户分页列表"""
    return Result.success(user_service.get_user_page(db,page,page_size,username),
                          message="获取用户分页列表成功")


@user_router.post("/add")
def add_user(data: AddUserRequest,current_admin: User = Depends(get_current_admin),db: Session = Depends(get_db)):
    """管理员新增用户"""
    return Result.success(user_service.add_user(db, data), message="新增用户成功")


@user_router.put("/admin/update")
def admin_update_user(data: AdminUpdateUserRequest,
                      current_admin: User = Depends(get_current_admin),
                      db: Session = Depends(get_db)):
    """管理员编辑用户信息（按账号定位）"""
    return Result.success(user_service.admin_update_user(db, data), message="用户信息更新成功")


@user_router.put("/admin/status")
def admin_set_user_status(data: AdminSetStatusRequest,
                          current_admin: User = Depends(get_current_admin),
                          db: Session = Depends(get_db)):
    """管理员启用/禁用用户（按账号定位）"""
    return Result.success(user_service.admin_set_status(db, data, current_admin), message="状态设置成功")
