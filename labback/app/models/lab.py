from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Lab(Base):
    __tablename__ = "lab"
    __table_args__ = {"comment": "实验室信息表"}
    name: Mapped[str] = mapped_column(String(255), comment="实验室名称", nullable=False)
    description: Mapped[str]= mapped_column(String(500),comment="简介",nullable=True)
    location: Mapped[str] = mapped_column(String(255), comment="实验室位置", nullable=True)
    # 容量是数字：数据库列用 Integer，类型标注用 int（原 Mapped[str] 与列类型不匹配）
    capacity: Mapped[int] = mapped_column(Integer, comment="实验室容量")
    open_time: Mapped[str] = mapped_column(String(20),comment="开放时间")
    close_time: Mapped[str] = mapped_column(String(20),comment="结束时间")
    img : Mapped[str] =mapped_column(String(100),comment="图片路径",nullable=True)
    status: Mapped[str] = mapped_column(String(255), comment="状态,0:禁用,1:启用", default="1", nullable=False)
