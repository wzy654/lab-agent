from app.models import User
from app.schemas.user import UserResponse


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
