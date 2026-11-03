// 认证模块
// 后端需实现：
//   POST /api/auth/login    { account, password } → { token, user }
//   POST /api/auth/logout
//   GET  /api/auth/me       → UserInfo

import { get, post } from './request'
import type { LoginResult, UserInfo } from './types'

export const authApi = {
  login(account: string, password: string) {
    return post<LoginResult>('/auth/login', { account, password })
  },

  logout() {
    return post<null>('/auth/logout')
  },

  me() {
    return get<UserInfo>('/auth/me')
  },
}
