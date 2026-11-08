#登陆权限服务
import random

from sqlalchemy.orm import Session

from app.exceptions import BizError
from app.models.User import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserResponse
from app.utils.jwt import create_jwt_token
from app.utils.password import verify_password, hash_password


def login(db: Session,data:LoginRequest):
    user = db.query(User).filter(User.user_name == data.user_name).first()
    if not user:
        raise BizError(message="账号不存在")
    if not verify_password(data.password, user.password):
        raise BizError(message="密码错误")
    if user.status != 1:
        raise BizError(message="账号已被禁用")
    token = create_jwt_token(user.id)
    return LoginResponse(user=UserResponse.model_validate(user), token=token)

def register(db: Session,data:RegisterRequest):
    user=db.query(User).filter(User.user_name == data.user_name).first()
    if user:
        raise BizError(message="账号已存在")
    # 姓名未填时生成默认名：「用户」+ 6位随机数
    name = data.name if data.name else f"用户{random.randint(100000, 999999)}"
    user=User(user_name=data.user_name,password=hash_password(data.password)
              ,name=name,status=1,role="student")
    db.add(user)
    # 提交事务
    db.commit()
    # 刷新用户信息
    db.refresh(user)

