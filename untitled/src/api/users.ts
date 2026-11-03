// 用户模块
// 后端需实现：
//   GET    /api/users      → UserInfo[]
//   POST   /api/users      { name, account, role, college, password } → UserInfo
//   PUT    /api/users/:id  同上 → UserInfo
//   DELETE /api/users/:id  → null

import { del, get, post, put } from './request'
import type { UserInfo } from './types'

export const userApi = {
  list() {
    return get<UserInfo[]>('/users')
  },

  create(data: {
    name: string
    account: string
    role: UserInfo['role']
    college: string
    password: string
  }) {
    return post<UserInfo>('/users', data)
  },

  update(id: number, data: Partial<UserInfo>) {
    return put<UserInfo>(`/users/${id}`, data)
  },

  remove(id: number) {
    return del<null>(`/users/${id}`)
  },
}
