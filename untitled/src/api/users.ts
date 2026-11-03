// ============================================================
// 用户模块：用户查询/管理的接口定义
// 后端已实现：
//   GET  /user/list?page=&page_size=&username= → PageResult<UserInfo>（需管理员）
//   POST /user/add → UserInfo（需管理员）
//   PUT  /user/admin/update → UserInfo（需管理员）
//   PUT  /user/admin/status → UserInfo（需管理员）
// 后端待实现：删除（下面已约定好接口格式）
// ============================================================

import { del, get, post, put } from '@/utils/request'
import type { PageResult, UserInfo } from './types'

export const userApi = {
  // 分页查询用户列表（需管理员 token，后端会校验角色）
  // page 页码（从 1 开始）、pageSize 每页条数、username 按姓名模糊搜索（可选）
  page(page: number, pageSize: number, username?: string) {
    return get<PageResult<UserInfo>>('/user/list', {
      page,
      page_size: pageSize, // 字段名以后端为准：后端参数叫 page_size
      username,            // undefined 的参数 axios 会自动丢弃，不会拼到 URL 上
    })
  },

  // 新增用户（需管理员 token，后端会校验角色）
  // 参数与后端 AddUserRequest 对齐：账号、姓名、密码、角色（不传默认 student）
  create(data: {
    user_name: string
    name: string
    role: UserInfo['role'] // 取 UserInfo 里 role 字段的类型，即 'admin' | 'student'
    password: string
  }) {
    return post<UserInfo>('/user/add', data)
  },

  // 管理员编辑用户信息（需管理员 token）
  // 以 user_name 定位用户；data 只传要修改的字段，后端没传的字段保持原值
  // 账号本身不可修改，所以参数里没有 user_name 的更新，它只作为定位用
  update(data: {
    user_name: string
    name?: string
    email?: string
    phone?: string
    role?: UserInfo['role']
  }) {
    return put<UserInfo>('/user/admin/update', data)
  },

  // 管理员启用/禁用用户（需管理员 token）
  // status：'1' 启用、'0' 禁用（与后端数据库约定一致）
  setStatus(user_name: string, status: '0' | '1') {
    return put<UserInfo>('/user/admin/status', { user_name, status })
  },

  // 删除用户
  remove(user_name: string) {
    return del<null>(`/users/${user_name}`) // 返回 null 表示没有数据体
  },
}
