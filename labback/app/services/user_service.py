from app.exceptions import BizError
from app.models import User
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

