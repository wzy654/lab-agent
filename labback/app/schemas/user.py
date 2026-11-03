from pydantic import BaseModel, ConfigDict
#继承BaseModel的原因
#数据契约”，这正是 FastAPI 相比 Flask 的核心优势所在。
class UserResponse(BaseModel):
    """用户响应"""
    user_name: str
    #密码不返回
    name: str
    role: str
    email: str | None
    phone: str | None
    avatar: str | None
    status: str
    #配置模型属性,对象可转换为json
    model_config = ConfigDict(from_attributes=True)

class UserUpdateRequest(BaseModel):
    """更新用户信息请求"""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None

class PasswordUpdateRequest(BaseModel):
    """更新密码请求"""
    old_password: str
    new_password: str
