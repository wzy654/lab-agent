#数据库连接

from sqlalchemy.orm import sessionmaker, DeclarativeBase, mapped_column,Mapped
from sqlalchemy import create_engine, DateTime
from .config import settings
from datetime import datetime, timedelta

#数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
)

#数据库会话工厂
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

def get_db():
    #获取数据库会话
    db = SessionLocal()
    #返回数据库会话
    try:
        yield db
    finally:
        #关闭数据库会话
        db.close()

#公共字段抽取
class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    create_time: Mapped[datetime] = (
        mapped_column(DateTime,default=datetime.now(), comment="创建时间"))
    update_time: Mapped[datetime] = (
        mapped_column(DateTime,default=datetime.now(), onupdate=datetime.now(), comment="更新时间"))
