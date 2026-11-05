
// Vue 3 的响应式 API：ref 创建一个「响应式数据容器」
// ref 的值变化时，用到它的页面会自动更新；.value 用来读写它的值
import { ref } from 'vue'
import { getUserInfo, logout, setToken, setUserInfo } from './auth'
import type { LoginResult, UserInfo } from '@/api/types'

// 包装为响应式对象：任何组件里调用 useUser() 拿到的 userInfo 都是同一个引用
// （模块级别的变量全局只有一份），所以一处更新、处处同步
const userInfo = ref(getUserInfo())

// 自定义组合式函数（Composable）：Vue 3 中复用逻辑的惯用写法，
// 函数名约定以 use 开头
export function useUser() {
  // 登录成功后调用：同时更新「localStorage 缓存」和「内存里的全局 userInfo」
  // 注意：只写 localStorage 不够——SPA 不刷新页面，内存变量不会自动重新读取，
  // 否则切换账号后头像等处会一直显示上一个用户，直到某个操作触发刷新
  function saveLoginData(data: LoginResult) {
    setToken(data.token)
    setUserInfo(data.user)
    userInfo.value = data.user
  }

  // 更新用户信息（如修改了个人资料）
  function updateUser(user: UserInfo) {
    setUserInfo(user)
    userInfo.value = user
  }

  // 从 localStorage 重新读取（其他标签页修改后同步用）
  function reloadUser() {
    userInfo.value = getUserInfo()
  }

  // 退出登录：清空 localStorage 缓存，并把内存里的全局 userInfo 重置为 null
  // 保证切换账号后页面上不会残留上一个用户的信息
  function clearUser() {
    logout()
    userInfo.value = null
  }

  return {
    userInfo,
    saveLoginData,
    updateUser,
    reloadUser,
    clearUser,
  }
}
