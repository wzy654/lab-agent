from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.User import User
from app.schemas.response import Result
from app.schemas.user import UserResponse

user_router = APIRouter(prefix="/user",tags=["用户信息"])

@user_router.get("/info")
def get_user_info(user: User = Depends(get_current_user)):
    """获取登录用户信息"""
    return Result.success(UserResponse.model_validate(user), message="获取用户信息成功")


