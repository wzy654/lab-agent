from app.database import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"comment": "用户表信息表"}

    user_name: Mapped[str] = mapped_column(String(50), comment="账号", nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), comment="密码", nullable=False)
    name: Mapped[str] = mapped_column(String(255), comment="昵称", nullable=False)
    role: Mapped[str] = mapped_column(String(255), comment="角色student/admin", nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), comment="邮箱", nullable=True)
    phone: Mapped[str | None] = mapped_column(String(255), comment="手机号", nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), comment="头像", nullable=True)
    status: Mapped[str] = mapped_column(String(255), comment="状态,0:禁用,1:启用", default="1", nullable=False)
