import asyncio
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.exceptions import BizError
from app.models import Equipment
from app.models.User import User
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.schemas.reservation import (ReservationCreateRequest,
                                     ReservationResponse,
                                     ReservationReviewRequest)
from app.schemas.response import PageResult


def _to_response(r: Reservation) -> ReservationResponse:
    """把预约模型对象转成响应模型，并通过 relationship 补齐关联名称

    兼容旧版 Pydantic：先 model_validate 转换基础字段，再单独赋值关联名称
    （r.user / r.lab / r.equipment 由外键 relationship 自动查关联表）。
    """
    response = ReservationResponse.model_validate(r)
    response.user_name = r.user.name
    response.lab_name = r.lab.name
    # 预约整间实验室时 equipment 为 None，设备名也返回 None
    response.equipment_name = r.equipment.name if r.equipment else None
    return response


def get_my_page(db: Session, current_user: User, page: int = 1,
                page_size: int = 10, status: int | None = None,
                days: int | None = None) -> PageResult:
    """我的预约分页：只查当前登录用户自己的预约记录

    days 可选：传 1/7/30 表示只看最近 1 天 / 1 周 / 1 个月内提交的预约
    （按提交时间 create_time 过滤），不传查全部。
    """
    query = db.query(Reservation).filter(Reservation.user_id == current_user.id)
    # 状态过滤：用 is not None 判断，避免 0（待审核）被当成假值跳过
    if status is not None:
        query = query.filter(Reservation.status == status)
    # 时间范围过滤：create_time 晚于「现在 - N 天」
    if days is not None:
        query = query.filter(Reservation.create_time >= datetime.now() - timedelta(days=days))
    total = query.count()
    # id 倒序：最新提交的排在最前面
    rows = (query.order_by(Reservation.id.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return PageResult(list=[_to_response(r) for r in rows], total=total)


def cancel_reservation(db: Session, current_user: User, reservation_id: int) -> None:
    """用户取消自己的预约：仅「待审核」状态可以取消"""
    reservation = db.get(Reservation, reservation_id)
    # 查不到、或不是自己的预约，统一报「预约不存在」，避免泄露别人的预约 id
    if not reservation or reservation.user_id != current_user.id:
        raise BizError(message="预约不存在")
    # 只有待审核（0）能取消：已通过的要先找管理员，已拒绝/已取消的无需再取消
    if reservation.status != 0:
        raise BizError(message="当前状态的预约无法取消")
    reservation.status = 3  # 3:已取消
    db.commit()


def get_admin_page(db: Session, page: int = 1, page_size: int = 10,
                   status: int | None = None) -> PageResult:
    """管理员预约审核分页：查所有人的预约，可按状态过滤"""
    query = db.query(Reservation)
    if status is not None:
        query = query.filter(Reservation.status == status)
    total = query.count()
    # id 倒序：最新提交的排在最前面，管理员优先处理新申请
    rows = (query.order_by(Reservation.id.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return PageResult(list=[_to_response(r) for r in rows], total=total)


def review_reservation(db: Session, data: ReservationReviewRequest) -> None:
    """管理员审核预约：对待审核的预约执行通过（1）或拒绝（2）"""
    reservation = db.get(Reservation, data.id)
    if not reservation:
        raise BizError(message="预约不存在")
    # 只有待审核（0）的预约能审核，不能重复审核或审核已取消的
    if reservation.status != 0:
        raise BizError(message="该预约已处理，无法重复审核")
    # 审核结果只允许 通过/拒绝 两个值
    if data.status not in (1, 2):
        raise BizError(message="审核结果不合法，只支持 1(通过) 或 2(拒绝)")
    reservation.status = data.status
    db.commit()


def create_reservation(db:Session,current_user:User ,data:ReservationCreateRequest):
    """创建预约"""
    now=datetime.now()
    current_date=now.strftime("%Y-%m-%d")
    current_time=now.strftime("%H:%M")
    if current_date>data.date:
        raise BizError(message="预约时间不能早于当前时间")
    if current_time>data.start_time and current_date==data.date:
        raise BizError(message="预约时间不能早于当前时间")
    if data.end_time<data.start_time:
        raise BizError(message="预约结束时间不能小于开始时间")

    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()
    if not lab:
        raise BizError(message="实验室不存在")
    if lab.status!=1:
        raise BizError(message="实验室已关闭")
    if lab.open_time>data.start_time:
        raise BizError(message="预约时间不能早于实验室开放时间")
    if lab.close_time<data.end_time:
        raise BizError(message="预约时间不能晚于实验室关闭时间")
    # 设备校验：只在「指定设备」时执行（equipment_id 为 None 表示预约整个实验室）
    if data.equipment_id is not None:
        equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        if not equipment:
            raise BizError(message="设备不存在")
        if equipment.status != 1:
            raise BizError(message="设备已关闭")
        # 校验设备确实挂在这个实验室下，防止拿 A 实验室的 id 配 B 实验室的设备
        if equipment.lab_id != data.lab_id:
            raise BizError(message="设备不属于该实验室")

    # ---------- 占用冲突检查 ----------
    # 先构建基础条件：同一实验室、同一天、时间段有交集、状态是待审核或已通过
    # （2 已拒绝 / 3 已取消 的预约不占用资源）
    # 时间交集判断：已有预约的开始时间 < 新预约的结束时间，且已有预约的结束时间 > 新预约的开始时间
    query = db.query(Reservation).filter(
        Reservation.lab_id == data.lab_id,
        Reservation.date == data.date,
        Reservation.status.in_([0, 1]),  # 0:待审核 1:已通过，这两种都算占用
        Reservation.start_time < data.end_time,
        Reservation.end_time > data.start_time,
    )
    if data.equipment_id is not None:
        # 预约某台设备：与「整间实验室的预约」或「这台设备自己的预约」冲突
        # （约整间说明实验室被整体占用，里面的设备自然也不能用）
        query = query.filter(
            (Reservation.equipment_id.is_(None)) | (Reservation.equipment_id == data.equipment_id)
        )
    # 预约整个实验室：不需要追加条件，该实验室任何重叠预约都算冲突
    # 注意：.filter() 返回新查询对象，必须重新赋值给 query（原写法 filter 结果被丢弃了）
    if query.first():
        raise BizError(message="所选时间已被预约，请换个时间或设备")

    reservation=Reservation(
        lab_id=data.lab_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        equipment_id=data.equipment_id,
        user_id=current_user.id,
        remark=data.remark,
        status=0,
    )
    db.add(reservation)
    db.commit()

def expire_pending_reservations() -> None:
    """过期待审核预约：预约时间已过仍处于待审核（0）的，自动置为已取消（3）"""
    db = SessionLocal()
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        now_hm = now.strftime("%H:%M")
        # 注意：这里必须用 .all() 拿记录对象，不能用 .update()——
        # .update() 是批量 UPDATE 语句，会把所有待审核预约直接改掉，返回的是行数不是记录
        items = db.query(Reservation).filter(Reservation.status == 0).all()
        changed = False
        for item in items:
            # 过期判断：预约日期已经过了，或是当天但开始时间已经过了
            if item.date < today or (item.date == today and item.start_time < now_hm):
                item.status = 3  # 3:已取消
                changed = True
        if changed:
            db.commit()
    finally:
        db.close()


async def run_expire_scan():
    """过期待审核预约扫描任务，每分钟扫描一次，将过期的预约自动取消"""
    while True:
        print("定时扫描中...")
        try:
            expire_pending_reservations()
        except Exception:
            # 后台任务的异常不会自动打印，必须自己兜底记录，否则崩了也无感知
            import traceback
            traceback.print_exc()
        await asyncio.sleep(60)  # 每分钟扫描一次

