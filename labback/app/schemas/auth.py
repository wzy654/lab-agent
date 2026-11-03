#登录请求体
from pydantic import BaseModel
#继承BaseModel的原因是为了使用pydantic的验证功能
class LoginRequest(BaseModel):
    user_name: str
    password: str

#登录响应体：用户信息 + token
from app.schemas.user import UserResponse
class LoginResponse(BaseModel):
    user: UserResponse
    token: str
