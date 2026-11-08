from http.client import UNAUTHORIZED

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import BizError, UnauthorizedError, ErrorCode
from app.models.User import User
from app.utils.jwt import decode_jwt_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """JWT验证"""
    user_id = decode_jwt_token(token)
    if not user_id:
        raise UnauthorizedError(UNAUTHORIZED)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BizError(ErrorCode.NOT_FOUND,message="用户不存在")
    if user.status != 1:
        raise BizError(ErrorCode.FORBIDDEN,message="用户已被禁用")
    return user

def get_current_admin(
        current_user: User = Depends(get_current_user)
        )-> User:
    """校验当前登录用户是否为管理员"""
    if current_user.role!="admin":
        raise BizError(ErrorCode.FORBIDDEN,message="无权限")
    return current_user
