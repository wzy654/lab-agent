// ============================================================
// 实验室模块：管理员端的增删改查接口定义
// 后端已实现（全部需管理员 token）：
//   GET    /lab/list?page=&page_size=&name= → PageResult<LabInfo>
//   POST   /lab/add → LabInfo
//   PUT    /lab/admin/update → LabInfo
//   PUT    /lab/admin/status → LabInfo
//   DELETE /lab/{id} → null
// ============================================================

import { del, get, post, put } from '@/utils/request'
import type { LabInfo, PageResult } from './types'

// 新增实验室的入参类型：name/capacity/开放/关闭时间必填，其余选填
export interface LabCreateData {
  name: string
  capacity: number
  open_time: string
  close_time: string
  description?: string
  location?: string
  img?: string
}

// 编辑实验室的入参类型：id 定位用；其余字段都可选，只传要改的
// img 特殊：传 null 表示「清空图片」，不传表示「保持原样」
export interface LabUpdateData {
  id: number
  name?: string
  description?: string
  location?: string
  capacity?: number
  open_time?: string
  close_time?: string
  img?: string | null
}

export const labApi = {
  // 分页查询实验室列表（需管理员 token）
  // page 页码（从 1 开始）、pageSize 每页条数、name 按名称模糊搜索（可选）
  page(page: number, pageSize: number, name?: string) {
    return get<PageResult<LabInfo>>('/lab/list', {
      page,
      page_size: pageSize, // 字段名以后端为准：后端参数叫 page_size
      name,                // undefined 的参数 axios 会自动丢弃，不会拼到 URL 上
    })
  },

  // 新增实验室（需管理员 token），参数与后端 LabAddRequest 对齐
  create(data: LabCreateData) {
    return post<LabInfo>('/lab/add', data)
  },

  // 编辑实验室（需管理员 token）：data 里必须带 id，其余只传要修改的字段
  update(data: LabUpdateData) {
    return put<LabInfo>('/lab/admin/update', data)
  },

  // 启用/禁用实验室（需管理员 token）：status 传 '0'（禁用）或 '1'（启用）
  setStatus(id: number, status: '0' | '1') {
    return put<LabInfo>('/lab/admin/status', { id, status })
  },

  // 删除实验室（需管理员 token）：RESTful 风格，id 拼在路径里
  remove(id: number) {
    return del<null>(`/lab/${id}`) // 返回 null 表示没有数据体
  },
}
