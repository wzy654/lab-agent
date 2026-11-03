from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.User import User
from app.schemas.response import Result
from app.schemas.user import UserUpdateRequest
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


