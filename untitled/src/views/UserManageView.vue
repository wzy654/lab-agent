<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi } from '@/api/users'
import type { UserInfo } from '@/api/types'

const users = ref<UserInfo[]>([])
const loading = ref(true)

const roleText: Record<UserInfo['role'], string> = {
  admin: '管理员',
  teacher: '教师',
  student: '学生',
}

onMounted(async () => {
  try {
    users.value = await userApi.list()
  } catch {
    ElMessage.error('用户列表加载失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
})

// TODO: 新增/编辑/禁用接入 userApi.create / update / remove
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary">新增用户</el-button>
    </div>

    <el-table v-loading="loading" :data="users" style="width: 100%">
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="account" label="学号 / 工号" width="140" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small" effect="plain">
            {{ roleText[row.role as UserInfo['role']] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="college" label="院系" min-width="150" />
      <el-table-column prop="monthly_bookings" label="本月预约次数" width="120" />
      <el-table-column label="操作" width="160">
        <template #default>
          <el-button link type="primary" size="small">编辑</el-button>
          <el-button link type="danger" size="small">禁用</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无数据，请确认后端 /api/users 接口已就绪" :image-size="80" />
      </template>
    </el-table>
  </div>
</template>

<style scoped>
.page {
  padding: 24px 32px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  color: #1f2d3d;
}
</style>
