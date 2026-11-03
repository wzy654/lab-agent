// 与后端约定的数据结构，FastAPI 的 Pydantic 模型请与此保持一致

export interface UserInfo {
  id: number
  name: string
  account: string
  role: 'admin' | 'teacher' | 'student'
  college: string
  monthly_bookings: number
}

export interface Lab {
  id: number
  name: string
  location: string
  capacity: number
  device_count: number
  is_open: boolean
}

export interface Device {
  id: number
  name: string
  model: string
  lab_id: number
  lab_name: string
  total: number
  available: number
}

export interface Booking {
  id: number
  lab_id: number
  lab_name: string
  user_name: string
  start_time: string
  end_time: string
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
}

/** 首页统计数据 */
export interface HomeStats {
  today_bookings: number
  today_bookings_delta: number
  free_labs: number
  total_labs: number
  pending_reviews: number
  monthly_usage_rate: number
}

/** AI 聊天 */
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

/** 登录返回 */
export interface LoginResult {
  token: string
  user: UserInfo
}
