// ============================================================
// 预约模块：创建 / 我的预约 / 取消 / 管理员审核接口定义
// 后端已实现：
//   POST /reservation          → 创建预约（登录用户即可）
//   GET  /reservation/my       → 我的预约分页（登录用户即可）
//   PUT  /reservation/cancel   → 取消自己的待审核预约（登录用户即可）
//   GET  /reservation/admin/list → 预约审核分页（需管理员）
//   PUT  /reservation/admin/review → 审核通过/拒绝（需管理员）
// 入参与后端 app/schemas/reservation.py 中的模型对齐
// ============================================================

import { get, post, put } from '@/utils/request'
import type { PageResult, ReservationInfo, ReservationStatus } from './types'

// 创建预约的入参类型
// equipment_id 可选：不传 = 预约整个实验室；传设备 id = 预约某台设备
export interface ReservationCreateData {
  lab_id: number
  equipment_id?: number | null
  /** 预约日期，"YYYY-MM-DD" 格式 */
  date: string
  /** 开始时间，"HH:mm" 格式 */
  start_time: string
  /** 结束时间，"HH:mm" 格式 */
  end_time: string
  /** 备注，选填 */
  remark?: string
}

export const reservationApi = {
  // 提交预约（成功后状态为「待审核」，等管理员审核）
  create(data: ReservationCreateData) {
    return post<null>('/reservation', data)
  },

  // 我的预约分页：status 可选，传 0/1/2/3 过滤对应状态，不传查全部
  // days 可选：传 1/7/30 表示只看最近 1 天 / 1 周 / 1 个月内提交的预约
  myPage(page: number, pageSize: number, status?: ReservationStatus, days?: number) {
    return get<PageResult<ReservationInfo>>('/reservation/my', {
      page,
      page_size: pageSize, // 字段名以后端为准：后端参数叫 page_size
      status,              // undefined 的参数 axios 会自动丢弃
      days,
    })
  },

  // 取消自己的预约（仅待审核状态可取消），按 id 定位
  cancel(id: number) {
    return put<null>('/reservation/cancel', { id })
  },

  // 预约审核分页（需管理员）：查所有人的预约，可按状态过滤
  adminPage(page: number, pageSize: number, status?: ReservationStatus) {
    return get<PageResult<ReservationInfo>>('/reservation/admin/list', {
      page,
      page_size: pageSize,
      status,
    })
  },

  // 审核预约（需管理员）：status 传 1（通过）或 2（拒绝）
  review(id: number, status: 1 | 2) {
    return put<null>('/reservation/admin/review', { id, status })
  },
}
