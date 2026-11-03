<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Lock, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { authApi } from '@/api/auth'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    // 对接后端登录接口：POST /api/auth/login
    const { token } = await authApi.login(form.username, form.password)
    localStorage.setItem('token', token)
    ElMessage.success('登录成功')
    router.push('/')
  } catch {
    ElMessage.error('用户名或密码错误，或后端服务未启动')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-brand">
        <h1>智能实验室预约系统</h1>
        <p>Smart Lab Reservation System</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
        <el-form-item prop="username">
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
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="login-btn" :loading="loading" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1c3d5a 0%, #1f6feb 60%, #34c3ff 100%);
}

.login-card {
  width: 380px;
  background: #fff;
  border-radius: 16px;
  padding: 40px 36px;
  box-shadow: 0 12px 40px rgba(0, 30, 60, 0.25);
}

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
  letter-spacing: 1px;
}

.login-btn {
  width: 100%;
}
</style>
