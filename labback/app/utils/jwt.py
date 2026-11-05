#jwt工具
import datetime
from http.client import UNAUTHORIZED

import jwt

from app.config import settings
from app.exceptions import BizError, UnauthorizedError


def create_jwt_token(user_id: int) -> str:
    """创建jwt token"""
    expire = datetime.datetime.now() + datetime.timedelta(hours=settings.JWT_EXPIRE_HOUR)

    payload = {
        "user_id": user_id,
        "exp": expire,  #exp 是 JWT 标准字段，验证时自动校验过期
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

def decode_jwt_token(token: str) -> int :
    """解码jwt token,返回user_id"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        # 必须用 UnauthorizedError（HTTP 401）：前端只在收到 401 时才自动跳登录页。
        # 如果用 BizError（默认 HTTP 400），过期时前端只会弹错误提示、不会跳转
        raise UnauthorizedError(UNAUTHORIZED, "登录已过期，请重新登录")
    except jwt.DecodeError:
        raise UnauthorizedError(UNAUTHORIZED, "登录凭证无效，请重新登录")

