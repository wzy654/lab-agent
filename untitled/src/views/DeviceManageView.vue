<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { deviceApi } from '@/api/devices'
import type { Device } from '@/api/types'

const devices = ref<Device[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    devices.value = await deviceApi.list()
  } catch {
    ElMessage.error('设备列表加载失败，请确认后端服务已启动')
  } finally {
    loading.value = false
  }
})

// TODO: 新增/编辑/删除接入 deviceApi.create / update / remove
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2>设备管理</h2>
      <el-button type="primary">新增设备</el-button>
    </div>

    <el-table v-loading="loading" :data="devices" style="width: 100%">
      <el-table-column prop="name" label="设备名称" min-width="160" />
      <el-table-column prop="model" label="型号" min-width="140" />
      <el-table-column prop="lab_name" label="所属实验室" min-width="150" />
      <el-table-column prop="total" label="总数" width="80" />
      <el-table-column prop="available" label="可借" width="80" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.available > 0 ? 'success' : 'danger'" size="small">
            {{ row.available > 0 ? '可借用' : '已借完' }}
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
        <el-empty description="暂无数据，请确认后端 /api/devices 接口已就绪" :image-size="80" />
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
