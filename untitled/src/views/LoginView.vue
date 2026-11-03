<script setup lang="ts">
// reactive：把一个对象变成响应式，适合表单这种多字段的数据
// ref：适合单个值的响应式（这里用于 DOM 引用和布尔开关）
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
// Element Plus 图标：输入框左侧的小图标
import { Lock, User } from '@element-plus/icons-vue'
// ElMessage：Element Plus 的消息弹窗（页面顶部滑出的小提示条）
import { ElMessage } from 'element-plus'
// FormInstance：表单实例的类型；FormRules：校验规则的类型（仅类型，无运行时代码）
import type { FormInstance, FormRules } from 'element-plus'
import { authApi } from '@/api/auth'
import { setToken, setUserInfo } from '@/utils/auth'

const router = useRouter()
// ref 指向模板里的 <el-form ref="formRef">，拿到表单实例后可调用 validate() 等方法
// ref<FormInstance>() 泛型里写类型，是「DOM/组件引用」的标准写法
const formRef = ref<FormInstance>()
const loading = ref(false) // 登录按钮的转圈状态，防止重复提交

// reactive 定义表单数据，v-model 双向绑定到输入框
const form = reactive({
  username: '',
  password: '',
})

// 表单校验规则：required 必填 / min 最小长度；trigger 表示何时触发校验
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }], // blur：失去焦点时
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}

async function handleLogin() {
  // validate() 校验整个表单，通过返回 true，不通过抛异常
  // .catch(() => false)：校验不通过时把异常转为 false，避免控制台报错
  const valid = await formRef.value?.validate().catch(() => false)
  // ?. 可选链：formRef.value 可能还没挂载（undefined），直接调用会报错
  if (!valid) return // 校验不通过，停止提交

  loading.value = true
  try {
    // 调用后端登录接口：POST /api/auth/login
    // await：等待接口返回；authApi.login 内部走 utils/request.ts 的封装
    // 解构赋值：从返回的 { user, token } 对象中直接取出两个字段
    const { token, user } = await authApi.login(form.username, form.password)
    setToken(token) // 存 token：之后所有请求会自动带上（见 utils/request.ts 请求拦截器）
    setUserInfo(user) // 存用户信息：页面显示当前用户用
    ElMessage.success('登录成功')
    router.push('/') // 跳转到首页，路由守卫检测到有 token 会放行
  } catch (err) {
    // 接口报错（密码错误/账号不存在/后端没启动）都会进到这里
    // err instanceof Error：判断错误类型，优先显示后端返回的具体错误信息
    ElMessage.error(err instanceof Error ? err.message : '登录失败，请稍后重试')
  } finally {
    // finally：无论成功失败都执行，恢复按钮状态
    loading.value = false
  }
}
</script>

<template>
  <!-- 登录页：全屏渐变背景 + 居中白色卡片，独立于主布局之外 -->
  <div class="login-page">
    <div class="login-card">
      <!-- 品牌区 -->
      <div class="login-brand">
        <h1>智能实验室预约系统</h1>
        <p>Smart Lab Reservation System</p>
      </div>

      <!-- el-form：Element Plus 表单组件，:model 绑定数据、:rules 绑定校验规则 -->
      <!-- @keyup.enter：键盘回车事件，回车快捷登录 -->
      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
        <!-- prop 对应 rules 里的字段名，校验错误信息会显示在这一项下方 -->
        <el-form-item prop="username">
          <!-- v-model：双向绑定，输入内容实时同步到 form.username -->
          <!-- :prefix-icon：输入框左侧图标 -->
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
          />
          <!-- show-password：显示「小眼睛」切换明文/密文 -->
        </el-form-item>
        <el-form-item>
          <!-- :loading 为 true 时按钮显示转圈并禁用，防止重复提交 -->
          <el-button type="primary" class="login-btn" :loading="loading" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
/* 整个页面：占满全屏，flex 布局让卡片水平垂直居中 */
/* linear-gradient：CSS 渐变背景，135deg 表示从左上到右下的方向 */
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1c3d5a 0%, #1f6feb 60%, #34c3ff 100%);
}

/* 登录卡片 */
.login-card {
  width: 380px;
  background: #fff;
  border-radius: 16px; /* 圆角 */
  padding: 40px 36px;
  box-shadow: 0 12px 40px rgba(0, 30, 60, 0.25); /* 阴影：右偏 移下移 模糊 颜色 */
}

/* 品牌文字区 */
.login-brand {
  text-align: center;
  margin-bottom: 32px;
}

.login-brand h1 {
  font-size: 20px;
  color: #1f2d3d;
  margin-bottom: 6px;
}

.login-brand p {
  font-size: 12px;
  color: #a0aec0;
  letter-spacing: 1px; /* 字间距 */
}

.login-btn {
  width: 100%; /* 按钮撑满表单宽度 */
}
</style>
