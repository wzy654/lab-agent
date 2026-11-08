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
  /** 状态，后端约定：0 禁用 / 1 启用（整数） */
  status: 0 | 1
}

// 与后端 LabResponse（app/schemas/lab.py）保持一致，后端字段为准
export interface LabInfo {
  id: number
  name: string
  description: string | null
  location: string | null
  /** 容量（人数） */
  capacity: number
  /** 开放时间，"HH:mm" 格式字符串，如 "08:00" */
  open_time: string
  /** 关闭时间，"HH:mm" 格式字符串，如 "22:00" */
  close_time: string
  /** 封面图片相对路径（如 uploads/xxx.png），可为空 */
  img: string | null
  /** 状态，后端约定：0 禁用 / 1 启用（整数） */
  status: 0 | 1
}

// 与后端 EquipmentResponse（app/schemas/equipment.py）保持一致，后端字段为准
export interface DeviceInfo {
  id: number
  /** 所属实验室的 id */
  lab_id: number
  /** 所属实验室的名称（后端从关联关系补充，前端只管显示） */
  lab_name: string
  name: string
  description: string | null
  /** 数量（台） */
  quantity: number
  /** 型号规格 */
  spec: string | null
  /** 图片相对路径（如 uploads/xxx.png），可为空 */
  img: string | null
  /** 状态，后端约定：0 禁用 / 1 启用（整数） */
  status: 0 | 1
}

// 实验室详情里嵌套的设备信息（精简版），对应后端 LabEquipmentItem
export interface LabEquipmentItem {
  id: number
  name: string
  spec: string | null
  quantity: number
  description: string | null
  img: string | null
  /** 状态，后端约定：0 禁用 / 1 启用（整数） */
  status: 0 | 1
}

// 实验室详情：基础信息 + 挂载的设备列表，对应后端 LabDetailResponse
export interface LabDetail extends LabInfo {
  equipment: LabEquipmentItem[]
}

/** 预约状态（整数）：0 待审核 / 1 已通过 / 2 已拒绝 / 3 已取消 */
export type ReservationStatus = 0 | 1 | 2 | 3

// 预约记录，与后端 ReservationResponse（app/schemas/reservation.py）保持一致
export interface ReservationInfo {
  id: number
  /** 预约人用户 id */
  user_id: number
  /** 预约人姓名（后端通过关联关系补充） */
  user_name: string
  lab_id: number
  /** 实验室名称（后端通过关联关系补充） */
  lab_name: string
  /** 设备 id，null 表示预约整个实验室 */
  equipment_id: number | null
  /** 设备名称（预约整间实验室时为 null） */
  equipment_name: string | null
  /** 预约日期，"YYYY-MM-DD" */
  date: string
  /** 开始时间，"HH:mm" */
  start_time: string
  /** 结束时间，"HH:mm" */
  end_time: string
  remark: string | null
  status: ReservationStatus
  /** 提交时间（后端 datetime 序列化为 ISO 字符串） */
  create_time: string | null
}

/** AI 聊天消息 */
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
