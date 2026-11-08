from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.User import User
from app.schemas.reservation import (ReservationCancelRequest,
                                     ReservationCreateRequest,
                                     ReservationReviewRequest)
from app.schemas.response import Result
from app.services import reservation_service

reservation_router = APIRouter(prefix="/reservation", tags=["预约"])


@reservation_router.post("")
def create_reservation(data: ReservationCreateRequest,
                       current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    """创建预约（登录用户即可）"""
    reservation_service.create_reservation(db, current_user, data)
    return Result.success(message="预约提交成功，请等待审核")


@reservation_router.get("/my")
def get_my_reservations(page: int = 1,
                        page_size: int = 10,
                        status: int | None = None,
                        days: int | None = None,
                        current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """我的预约分页：只返回当前登录用户自己的预约记录

    days 可选：传 1/7/30 表示只看最近 1 天 / 1 周 / 1 个月内提交的预约
    """
    return Result.success(
        reservation_service.get_my_page(db, current_user, page, page_size, status, days),
        message="获取我的预约成功",
    )


@reservation_router.put("/cancel")
def cancel_reservation(data: ReservationCancelRequest,
                       current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    """取消预约：只能取消自己的、且处于待审核状态的预约"""
    reservation_service.cancel_reservation(db, current_user, data.id)
    return Result.success(message="预约已取消")


@reservation_router.get("/admin/list")
def get_admin_reservations(page: int = 1,
                           page_size: int = 10,
                           status: int | None = None,
                           current_admin: User = Depends(get_current_admin),
                           db: Session = Depends(get_db)):
    """预约审核列表：管理员查看所有人的预约，可按状态过滤"""
    return Result.success(
        reservation_service.get_admin_page(db, page, page_size, status),
        message="获取预约列表成功",
    )


@reservation_router.put("/admin/review")
def review_reservation(data: ReservationReviewRequest,
                       current_admin: User = Depends(get_current_admin),
                       db: Session = Depends(get_db)):
    """审核预约：对待审核的预约执行通过（1）或拒绝（2）"""
    reservation_service.review_reservation(db, data)
    return Result.success(message="审核完成")
