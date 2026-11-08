# 预约信息表
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.User import User
from app.models.equipment import Equipment
from app.models.lab import Lab


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = {"comment": "预约信息表"}

    # 物理外键：user_id 必须是 user 表里真实存在的用户，数据库层面兜底拦脏数据
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), comment="预约者id", nullable=False
    )
    # 物理外键：lab_id 必须指向 lab 表里真实存在的实验室
    lab_id: Mapped[int] = mapped_column(
        ForeignKey("lab.id"), comment="实验室id", nullable=False
    )
    # 物理外键 + 可空：equipment_id 为空表示「预约整个实验室」，有值表示「预约某台设备」
    equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipment.id"), comment="设备id", nullable=True
    )
    date: Mapped[str] = mapped_column(String(20), comment="预约日期", nullable=False)
    start_time: Mapped[str] = mapped_column(String(20), comment="开始时间", nullable=False)
    end_time: Mapped[str] = mapped_column(String(20), comment="结束时间", nullable=False)
    remark: Mapped[str | None] = mapped_column(String(255), comment="备注", nullable=True)
    status: Mapped[int] = mapped_column(
        comment="预约状态0:待审核，1:已通过，2:已拒绝，3:已取消",
        nullable=False,
        default=0,
    )

    # relationship：让代码里能直接写 reservation.user.name、reservation.lab.name
    # 拿到关联对象，不用手动再查一次表。SQLAlchemy 会根据上面的外键自动推断关联关系。
    # user / lab 必然存在（非空外键），所以类型是单个对象；
    # equipment 可能没有（空 = 预约实验室），所以类型标注为 Equipment | None
    user: Mapped[User] = relationship()
    lab: Mapped[Lab] = relationship()
    equipment: Mapped[Equipment | None] = relationship()
