from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.lab import Lab


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = {"comment": "实验室设备表"}

    # 外键指向 lab 表的主键：注意表名是 "lab"（与 Lab 模型的 __tablename__ 一致），
    # 原来写的 "labs.id" 是不存在的表名，会导致建表直接报错
    lab_id: Mapped[int] = mapped_column(ForeignKey("lab.id"), comment="所属实验室", nullable=False)
    name: Mapped[str] = mapped_column(String(255), comment="设备名称", nullable=False)
    description: Mapped[str] = mapped_column(String(500), comment="说明", nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, comment="数量",default=1)
    spec : Mapped[str|None] =mapped_column(String(100),comment="型号规格")
    img: Mapped[str] = mapped_column(String(100), comment="图片路径", nullable=True)
    # 状态改为整数：0 禁用 / 1 启用（原来是字符串 "0"/"1"）
    status: Mapped[int] = mapped_column(Integer, comment="状态,0:禁用,1:启用", default=1, nullable=False)

    lab: Mapped[Lab] =relationship()