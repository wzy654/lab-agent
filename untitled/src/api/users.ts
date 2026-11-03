// ============================================================
// 用户模块：用户查询/管理的接口定义
// 后端已实现：
//   GET /user/list?page=&page_size=&username= → PageResult<UserInfo>（需管理员）
// 后端待实现：新增 / 修改 / 删除（下面已约定好接口格式）
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

  // 新增用户。参数 data 是一个对象，冒号后写的是每个字段的类型
  // email?: 表示可选字段，调用时可以不传
  create(data: {
    user_name: string
    name: string
    role: UserInfo['role'] // 取 UserInfo 里 role 字段的类型，即 'admin' | 'student'
    password: string
    email?: string | null
    phone?: string | null
  }) {
    return post<UserInfo>('/users', data)
  },

  // 修改用户：以 user_name 定位用户，data 只传要修改的字段
  // Partial<UserInfo>：TS 工具类型，表示「UserInfo 的所有字段都变成可选」
  update(user_name: string, data: Partial<UserInfo>) {
    return put<UserInfo>(`/users/${user_name}`, data)
    // `...${user_name}` 是模板字符串：把变量拼进 URL，如 /users/zhangsan
  },

  // 删除用户
  remove(user_name: string) {
    return del<null>(`/users/${user_name}`) // 返回 null 表示没有数据体
  },
}
