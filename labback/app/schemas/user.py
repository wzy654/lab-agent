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

class AddUserRequest(BaseModel):
    """新增用户信息请求"""
    user_name: str
    password: str
    name: str
    # 角色：管理员新增时可指定，不传默认为普通学生
    role: str = "student"

class AdminUpdateUserRequest(BaseModel):
    """管理员编辑用户信息请求（按 user_name 定位用户）"""
    user_name: str
    # 以下字段都是可选：只更新显式传入的字段，没传的保持原值
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None

class AdminSetStatusRequest(BaseModel):
    """管理员启用/禁用用户请求"""
    user_name: str
    status: str  # "0"禁用 "1"启用

