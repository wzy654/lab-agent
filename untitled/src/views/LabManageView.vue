<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { labApi } from '@/api/labs'
import type { Lab } from '@/api/types'

const labs = ref<Lab[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    labs.value = await labApi.list()
  } catch {
    ElMessage.error('实验室列表加载失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
})

// TODO: 新增/编辑/删除接入 labApi.create / update / remove
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2>实验室管理</h2>
      <el-button type="primary">新增实验室</el-button>
    </div>

    <el-table v-loading="loading" :data="labs" style="width: 100%">
      <el-table-column prop="name" label="实验室名称" min-width="160" />
      <el-table-column prop="location" label="位置" min-width="120" />
      <el-table-column prop="capacity" label="容量" width="80" />
      <el-table-column prop="device_count" label="设备数" width="80" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_open ? 'success' : 'info'" size="small">
            {{ row.is_open ? '开放中' : '已关闭' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default>
          <el-button link type="primary" size="small">编辑</el-button>
          <el-button link type="danger" size="small">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无数据，请确认后端 /api/labs 接口已就绪" :image-size="80" />
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
