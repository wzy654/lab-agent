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

/** 文件上传接口（POST /files/upload）返回的文件信息 */
export interface UploadResult {
  /** 原始文件名，如 66.png */
  origin_name: string
  /** 磁盘上保存的唯一文件名 */
  file_name: string
  /** 文件大小（字节） */
  size: number | null
  /** 相对路径（如 uploads/xxx.png），存库/显示都用它 */
  url: string
}

/** 分页查询的通用返回结构，对应后端 PageResult（app/schemas/response.py） */
export interface PageResult<T> {
  /** 当前页的数据列表 */
  list: T[]
  /** 满足条件的总条数（分页控件靠它算总页数） */
  total: number
}

/** 登录返回 */
export interface LoginResult {
  token: string
  user: UserInfo
}
