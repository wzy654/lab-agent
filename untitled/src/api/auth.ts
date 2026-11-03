// ============================================================
// 认证模块：登录相关的接口定义
// 调用链：页面组件 → 这里的 authApi → utils/request.ts 的封装 → 后端 FastAPI
// ============================================================

// get / post 是 utils/request.ts 暴露的快捷请求方法
import { get, post } from '@/utils/request'
// 只导入类型：LoginResult 是登录返回结构，UserInfo 是用户信息结构
import type { LoginResult, UserInfo } from './types'

export const authApi = {
  // 登录：POST /auth/login
  // 注意：后端 LoginRequest 的字段叫 user_name，前端表单习惯叫 account，
  // 所以发送时要做一次字段名转换（以后端为准）
  login(account: string, password: string) {
    return post<LoginResult>('/auth/login', { user_name: account, password })
  },

  // 获取当前登录用户信息：GET /user/info（请求会自动带 token，见请求拦截器）
  me() {
    return get<UserInfo>('/user/info')
  },
}
