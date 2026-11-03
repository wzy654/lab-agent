// ============================================================
// 登录凭证（token）和用户信息的本地缓存管理
// localStorage：浏览器提供的本地存储，数据永久保存，关浏览器也不丢
//   常用 API：getItem(key) 读 / setItem(key, value) 写 / removeItem(key) 删
// 为什么统一封装？全项目只在这一处直接操作 localStorage，
// 以后想换存储方式（如 sessionStorage）只需改这一个文件
// ============================================================

// import type：只导入类型定义，不会产生实际的运行时导入
import type { UserInfo } from '@/api/types'

// 存储的键名，定义为常量避免各处手写字符串写错
const TOKEN_KEY = 'token'
const USER_KEY = 'userInfo'

// ---------- token 相关 ----------

// 读取 token。路由守卫和请求封装都靠它判断「是否已登录」
export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

// 登录成功后保存 token
export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

// 退出登录 / token 失效时删除 token
export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

// ---------- 用户信息相关 ----------

// 读取用户信息。localStorage 只能存字符串，
// 所以存的时候用 JSON.stringify 转成字符串，读的时候用 JSON.parse 解析回对象
export function getUserInfo(): UserInfo | null {
  const str = localStorage.getItem(USER_KEY)
  return str ? JSON.parse(str) : null // 三元表达式：有值就解析，没值返回 null
}

// 登录成功后保存用户信息（对象 → JSON 字符串）
export function setUserInfo(userInfo: UserInfo) {
  localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
}

// 删除用户信息
export function removeUserInfo() {
  localStorage.removeItem(USER_KEY)
}

// ---------- 登出 ----------

// 登出：清空本地缓存的 token 和用户信息
// 注：后端暂无登出接口，前端清缓存即可完成登出
export function logout() {
  removeToken()
  removeUserInfo()
}
