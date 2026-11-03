<script setup lang="ts">
// <script setup>：Vue 3 组合式 API 的语法糖，
// 里面定义的变量/函数在 <template> 模板中可以直接使用，无需 return

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
const loading = ref(false) // 提交按钮的转圈状态，防止重复提交

// 当前表单模式：'login' 登录 / 'register' 注册，登录卡片上直接切换
const mode = ref<'login' | 'register'>('login')

// reactive 定义表单数据，v-model 双向绑定到输入框
// name 只在注册模式下使用（后端 RegisterRequest 的可选字段）
const form = reactive({
  username: '', // 账号（后端字段叫 user_name，发送时做了转换）
  password: '',
  confirmPassword: '', // 确认密码：纯前端校验用，不会发给后端
  name: '', // 姓名/昵称：注册时选填
})

// 表单校验规则：required 必填 / min 最小长度；trigger 表示何时触发校验
//Rules 里每个字段的规则是数组，数组里可以写多条规则，全部通过才算合格
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }], // blur：失去焦点时
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  // 确认密码：validator 是自定义校验，value 是当前输入框的值
  // callback() 无参调用表示校验通过，传 Error 表示校验失败
  confirmPassword: [
    {
      required: true,
      message: '请再次输入密码',
      trigger: 'blur',
    },
    {
      validator: (_rule, value: string, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 注册模式和登录模式可以共用一套 rules 的基础上，这里做增量处理：
// 切换模式时先清空上一次的校验提示，避免残留红色报错
function switchMode(m: 'login' | 'register') {
  mode.value = m
  formRef.value?.clearValidate() // 清除表单的校验状态
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

async function handleRegister() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    // 调用后端注册接口：POST /api/auth/register
    // 确认密码只在前端校验，不发送；姓名是可选字段，为空就不传
    await authApi.register(form.username, form.password, form.name)
    ElMessage.success('注册成功，请登录')
    switchMode('login') // 注册完成切回登录模式
    form.password = ''
    form.confirmPassword = ''
  } catch (err) {
    // 后端返回的「账号已存在」等业务错误会在这里被捕获并显示
    ElMessage.error(err instanceof Error ? err.message : '注册失败，请稍后重试')
  } finally {
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
      <!-- @keyup.enter：键盘回车事件，回车提交当前模式 -->
      <!-- 动态绑定事件：登录模式触发 handleLogin，注册模式触发 handleRegister -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        size="large"
        @keyup.enter="mode === 'login' ? handleLogin() : handleRegister()"
      >
        <el-form-item prop="username">
          <!-- v-model：双向绑定，输入内容实时同步到 form.username -->
          <!-- :prefix-icon：输入框左侧图标 -->
          <el-input
            v-model="form.username"
            :placeholder="mode === 'login' ? '用户名' : '设置用户名（学号/工号）'"
            :prefix-icon="User"
          />
        </el-form-item>
        <!-- 注册模式才显示姓名输入框（v-if 条件渲染） -->
        <el-form-item v-if="mode === 'register'" prop="name">
          <el-input v-model="form.name" placeholder="姓名（选填）" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="mode === 'login' ? '密码' : '设置密码（至少 6 位）'"
            :prefix-icon="Lock"
            show-password
          />
          <!-- show-password：显示「小眼睛」切换明文/密文 -->
        </el-form-item>
        <!-- 确认密码：仅注册模式显示 -->
        <el-form-item v-if="mode === 'register'" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <!-- :loading 为 true 时按钮显示转圈并禁用，防止重复提交 -->
          <!-- 按钮文字随模式变化：登录 / 注册 -->
          <el-button
            type="primary"
            class="login-btn"
            :loading="loading"
            @click="mode === 'login' ? handleLogin() : handleRegister()"
          >
            {{ mode === 'login' ? '登 录' : '注 册' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 底部切换入口：登录 ←→ 注册 -->
      <div class="switch-row">
        <template v-if="mode === 'login'">
          还没有账号？
          <el-link type="primary" :underline="false" @click="switchMode('register')">
            去注册
          </el-link>
        </template>
        <template v-else>
          已有账号？
          <el-link type="primary" :underline="false" @click="switchMode('login')">
            去登录
          </el-link>
        </template>
      </div>
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
  box-shadow: 0 12px 40px rgba(0, 30, 60, 0.25); /* 阴影：右偏 下移 模糊 颜色 */
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

/* 底部「去注册 / 去登录」切换行 */
.switch-row {
  text-align: center;
  font-size: 13px;
  color: #909399;
}
</style>
