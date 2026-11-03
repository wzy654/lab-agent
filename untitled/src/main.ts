import './assets/main.css'

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import { ElMessage } from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(router)
app.use(ElementPlus)
app.mount('#app')

// ============ 全局兜底：未处理的 Promise 异常统一弹出提示 ============
// 背景：async 函数里请求失败如果没人 catch，异常会被静默吞掉（控制台有红字但页面无反应）
// 这里兜住所有「没人接」的异常并弹出提示，保证用户永远能看到失败原因
window.addEventListener('unhandledrejection', (event) => {
  const reason = event.reason
  // 只提示真正的 Error 对象（如请求拦截器抛出的「旧密码错误」）
  // 表单校验不通过时 el-form 的 validate() 也会 reject，但它 reject 的是字段对象不是 Error，
  // 且红字已显示在输入框下方，不需要弹提示，这里跳过
  if (reason instanceof Error && reason.message) {
    ElMessage.error(reason.message)
    event.preventDefault() // 已提示过，阻止浏览器控制台重复报错
  }
})
