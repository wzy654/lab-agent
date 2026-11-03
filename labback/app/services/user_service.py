import random

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import BizError
from app.models import User
from app.schemas.response import PageResult
from app.schemas.user import UserResponse
from app.utils.password import hash_password, verify_password


def get_user_info(user: User)->UserResponse:
    """获取用户信息"""
    return UserResponse.model_validate(user)


def update_user_info(db, user, data):
    """更新用户信息"""
    # 只更新请求里显式传了的字段（exclude_unset），没传的字段保持原值
    dump = data.model_dump(exclude_unset=True)
    for field, value in dump.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
def update_password(db, user, data):
    """更新用户密码"""
    # 校验旧密码是否正确（user.password 是数据库里的 bcrypt 哈希值）
    if not verify_password(data.old_password, user.password):
        raise BizError(400,"旧密码错误")
    # 校验新密码是否符合要求
    if data.new_password==data.old_password:
        raise BizError(400,"新密码不能与旧密码相同")
    # 更新密码
    user.password = hash_password(data.new_password)
    db.commit()

def get_user_page(
        db: Session = Depends(get_db),
        page: int = 1,
        page_size: int = 10,
        username: str | None=None,
):
    """获取用户分页列表"""
    query = db.query(User)
    if username:
        query = query.filter(User.name.like(f"%{username}%"))
    total = query.count()
    # 分页查询
    users = query.order_by(User.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    return PageResult(
        list=[UserResponse.model_validate(user) for user in users],
        total=total,
    )

def add_user(db, data):
    """新增用户"""
    # 校验角色是否合法（只允许 student / admin 两种）
    if data.role not in ("student", "admin"):
        raise BizError(message="角色不合法，只支持 student 或 admin")
    user = db.query(User).filter(User.user_name == data.user_name).first()
    if user:
        raise BizError(message="账号已存在")
    # 姓名未填时生成默认名：「用户」+ 6位随机数
    name = data.name if data.name else f"用户{random.randint(100000, 999999)}"
    user = User(user_name=data.user_name, password=hash_password(data.password)
                , name=name, status="1", role=data.role)
    db.add(user)
    # 提交事务
    db.commit()
    # 刷新用户信息（拿到数据库生成的完整字段）
    db.refresh(user)
    # 返回新增用户的响应模型，供前端刷新列表使用
    return UserResponse.model_validate(user)


def admin_update_user(db, data):
    """管理员编辑用户信息（按 user_name 定位目标用户）"""
    # 先按账号找到要编辑的用户，找不到说明账号有误或已被删除
    user = db.query(User).filter(User.user_name == data.user_name).first()
    if not user:
        raise BizError(message="账号不存在")
    # 角色如果传了，校验合法性（只允许 student / admin 两种）
    if data.role is not None and data.role not in ("student", "admin"):
        raise BizError(message="角色不合法，只支持 student 或 admin")
    # 只更新请求里显式传了的字段（exclude_unset），没传的字段保持原值
    # user_name 是定位用的，不参与更新
    dump = data.model_dump(exclude_unset=True, exclude={"user_name"})
    for field, value in dump.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def admin_set_status(db, data, current_admin):
    """管理员启用/禁用用户"""
    # 先按账号找到目标用户，找不到说明账号有误
    user = db.query(User).filter(User.user_name == data.user_name).first()
    if not user:
        raise BizError(message="账号不存在")
    # 校验状态值合法性（"0"禁用 / "1"启用，与数据库约定一致）
    if data.status not in ("0", "1"):
        raise BizError(message="状态不合法，只支持 0(禁用) 或 1(启用)")
    # 禁止管理员禁用自己正在使用的账号，防止把自己锁在系统外
    if user.user_name == current_admin.user_name and data.status == "0":
        raise BizError(message="不能禁用当前登录的管理员账号")
    user.status = data.status
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
