#登录接口，相当与controller

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import BizError
from app.models.User import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.response import Result
from app.schemas.user import UserResponse
from app.utils.jwt import create_jwt_token
from app.utils.password import verify_password

auth_router = APIRouter(prefix="/auth",tags=["权限验证"])

@auth_router.post(path="/login", response_model=Result[LoginResponse])
def login(data: LoginRequest,db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_name == data.user_name).first()
    if not user:
        raise BizError(message="账号不存在")
    if not verify_password(data.password, user.password):
        raise BizError(message="密码错误")
    if user.status !="1":
        raise BizError(message="账号已被禁用")
    token = create_jwt_token(user.id)
    return Result.success(LoginResponse(user=UserResponse.model_validate(user), token=token), message="登录成功")
