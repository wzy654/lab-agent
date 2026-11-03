// ============================================================
// 认证模块：登录相关的接口定义
// 调用链：页面组件 → 这里的 authApi → utils/request.ts 的封装 → 后端 FastAPI
// ============================================================

// get / post 是 utils/request.ts 暴露的快捷请求方法
import { get, post, put } from '@/utils/request'
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

  // 注册：POST /auth/register
  // 后端 RegisterRequest 字段：user_name（账号）、password、name（昵称，可选）
  // 注册成功后端不返回数据（data 为 null），只返回 message「注册成功」
  register(user_name: string, password: string, name?: string) {
    return post<null>('/auth/register', { user_name, password, name: name || null })
  },

  // 修改当前登录用户的个人信息：PUT /user/update
  // 只能改姓名/邮箱/手机号/头像；账号和角色由 token 决定，接口本身不支持改
  // Partial<...> 表示四个字段都可选，只传要改的
  updateProfile(data: {
    name?: string
    email?: string | null
    phone?: string | null
    avatar?: string | null
  }) {
    return put<UserInfo>('/user/update', data)
  },
}
