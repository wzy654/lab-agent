// 首页与预约模块
// 后端需实现：
//   GET /api/home/stats    → HomeStats
//   GET /api/bookings?limit=5 → Booking[]（最近预约）
//   POST /api/bookings     { lab_id, start_time, end_time } → Booking

import { get, post } from './request'
import type { Booking, HomeStats } from './types'

export const homeApi = {
  stats() {
    return get<HomeStats>('/home/stats')
  },

  recentBookings(limit = 5) {
    return get<Booking[]>(`/bookings?limit=${limit}`)
  },
}

export const bookingApi = {
  create(data: { lab_id: number; start_time: string; end_time: string }) {
    return post<Booking>('/bookings', data)
  },
}
