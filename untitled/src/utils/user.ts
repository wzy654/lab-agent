
// Vue 3 的响应式 API：ref 创建一个「响应式数据容器」
// ref 的值变化时，用到它的页面会自动更新；.value 用来读写它的值
import { ref } from 'vue'
import { getUserInfo, setToken, setUserInfo } from './auth'
import type { LoginResult, UserInfo } from '@/api/types'

// 包装为响应式对象：任何组件里调用 useUser() 拿到的 userInfo 都是同一个引用
// （模块级别的变量全局只有一份），所以一处更新、处处同步
const userInfo = ref(getUserInfo())

// 自定义组合式函数（Composable）：Vue 3 中复用逻辑的惯用写法，
// 函数名约定以 use 开头
export function useUser() {
  // 登录成功后调用：保存 token 和用户信息
  function saveLoginData(data: LoginResult) {
    setToken(data.token)
    setUserInfo(data.user)
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

  return {
    userInfo,
    saveLoginData,
    updateUser,
    reloadUser,
  }
}
