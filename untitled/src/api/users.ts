// ============================================================
// 用户模块：用户增删改查的接口定义
// 后端已实现：GET /user/info（当前登录用户信息）
// 后端待实现：用户列表 / 新增 / 修改 / 删除（下面已约定好接口格式）
//   GET    /users             → UserInfo[]
//   POST   /users             { user_name, name, role, password, ... } → UserInfo
//   PUT    /users/:user_name  同上 → UserInfo
//   DELETE /users/:user_name  → null
// ============================================================

import { del, get, post, put } from '@/utils/request'
import type { UserInfo } from './types'

export const userApi = {
  // 获取用户列表。UserInfo[] 表示「UserInfo 类型的数组」
  list() {
    return get<UserInfo[]>('/users')
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
