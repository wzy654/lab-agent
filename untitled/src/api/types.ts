// 与后端约定的数据结构，FastAPI 的 Pydantic 模型请与此保持一致

// 与后端 UserResponse（app/schemas/user.py）保持一致，后端字段为准
export interface UserInfo {
  user_name: string
  name: string
  /** 角色，后端约定：student / admin */
  role: 'admin' | 'student'
  email: string | null
  phone: string | null
  avatar: string | null
  /** 状态，后端约定：0 禁用 / 1 启用 */
  status: '0' | '1'
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
