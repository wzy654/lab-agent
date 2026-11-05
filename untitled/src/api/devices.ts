// ============================================================
// 设备模块：管理员端的增删改查接口定义
// 后端已实现（全部需管理员 token）：
//   GET    /equipment/list?page=&page_size=&name=&lab_id= → PageResult<DeviceInfo>
//   POST   /equipment/add → DeviceInfo
//   PUT    /equipment/admin/update → DeviceInfo
//   PUT    /equipment/admin/status → DeviceInfo
//   DELETE /equipment/{id} → null
// ============================================================

import { del, get, post, put } from '@/utils/request'
import type { DeviceInfo, PageResult } from './types'

// 新增设备的入参类型：lab_id/name 必填，数量默认 1，其余选填
export interface DeviceCreateData {
  lab_id: number
  name: string
  quantity: number
  spec?: string
  description?: string
  img?: string
}

// 编辑设备的入参类型：id 定位用；其余字段都可选，只传要改的
// img 特殊：传 null 表示「清空图片」，不传表示「保持原样」
export interface DeviceUpdateData {
  id: number
  lab_id?: number
  name?: string
  description?: string
  quantity?: number
  spec?: string
  img?: string | null
}

export const deviceApi = {
  // 分页查询设备列表（需管理员 token）
  // page 页码（从 1 开始）、pageSize 每页条数、name 按名称模糊搜索、lab_id 按实验室过滤（都可选）
  page(page: number, pageSize: number, name?: string, labId?: number) {
    return get<PageResult<DeviceInfo>>('/equipment/list', {
      page,
      page_size: pageSize, // 字段名以后端为准：后端参数叫 page_size
      name,                // undefined 的参数 axios 会自动丢弃，不会拼到 URL 上
      lab_id: labId,
    })
  },

  // 新增设备（需管理员 token），参数与后端 EquipmentAddRequest 对齐
  create(data: DeviceCreateData) {
    return post<DeviceInfo>('/equipment/add', data)
  },

  // 编辑设备（需管理员 token）：data 里必须带 id，其余只传要修改的字段
  update(data: DeviceUpdateData) {
    return put<DeviceInfo>('/equipment/admin/update', data)
  },

  // 启用/禁用设备（需管理员 token）：status 传 '0'（禁用）或 '1'（启用）
  setStatus(id: number, status: '0' | '1') {
    return put<DeviceInfo>('/equipment/admin/status', { id, status })
  },

  // 删除设备（需管理员 token）：RESTful 风格，id 拼在路径里
  remove(id: number) {
    return del<null>(`/equipment/${id}`) // 返回 null 表示没有数据体
  },
}
