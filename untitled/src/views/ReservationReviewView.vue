<script setup lang="ts">
// <script setup>：Vue 3 组合式 API 的语法糖，
// 里面定义的变量/函数在 <template> 模板中可以直接使用，无需 return

import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reservationApi } from '@/api/reservations'
import type { ReservationInfo, ReservationStatus } from '@/api/types'

// ---------- 列表状态 ----------
const list = ref<ReservationInfo[]>([])  // 当前页的预约记录（所有人的）
const loading = ref(true)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 状态过滤：'' 表示全部；0 待审核 / 1 已通过 / 2 已拒绝 / 3 已取消
const statusFilter = ref<'' | ReservationStatus>('')

// 状态 → 中文文案 + 标签颜色的映射表，模板里按 status 取用
const statusMeta: Record<ReservationStatus, { text: string; tag: 'warning' | 'success' | 'danger' | 'info' }> = {
  0: { text: '待审核', tag: 'warning' },
  1: { text: '已通过', tag: 'success' },
  2: { text: '已拒绝', tag: 'danger' },
  3: { text: '已取消', tag: 'info' },
}

// 加载预约列表：翻页、切换状态过滤后的刷新都走这一个函数
async function loadList() {
  loading.value = true
  try {
    const result = await reservationApi.adminPage(
      page.value,
      pageSize.value,
      // '' 表示不过滤，传 undefined 让 axios 丢弃这个参数
      statusFilter.value === '' ? undefined : statusFilter.value,
    )
    list.value = result.list
    total.value = result.total
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '预约列表加载失败')
  } finally {
    loading.value = false
  }
}

// 切换状态过滤：从第 1 页重新查
function handleStatusChange() {
  page.value = 1
  loadList()
}

// el-pagination 的页码变化回调
function handlePageChange(newPage: number) {
  page.value = newPage
  loadList()
}

// 审核操作：通过（1）或拒绝（2），仅待审核状态可操作，后端还会再校验一次
async function handleReview(row: ReservationInfo, result: 1 | 2) {
  const actionText = result === 1 ? '通过' : '拒绝'
  try {
    // 确认弹窗：显示预约的关键信息，避免审核错行
    await ElMessageBox.confirm(
      `确定要${actionText}「${row.user_name}」预约「${row.lab_name}」` +
      `${row.date} ${row.start_time}~${row.end_time} 的申请吗？`,
      `预约${actionText}`,
      { type: result === 1 ? 'success' : 'warning', confirmButtonText: `确定${actionText}`, cancelButtonText: '取消' },
    )
  } catch {
    return // 用户点了取消，什么都不做
  }
  try {
    await reservationApi.review(row.id, result)
    ElMessage.success(`已${actionText}该预约`)
    loadList() // 刷新列表，该行状态更新
  } catch (e) {
    // 失败提示（如「该预约已处理，无法重复审核」——别人先审了一步时会出现）
    ElMessage.error(e instanceof Error ? e.message : '审核操作失败')
  }
}

// 提交时间的展示格式：ISO 字符串 → 本地化文本
function fmtTime(iso: string | null) {
  return iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'
}

// 首屏加载
onMounted(loadList)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2>预约审核</h2>
      <div class="header-actions">
        <!-- 状态过滤按钮：切换后从第 1 页重新查询 -->
        <el-radio-group v-model="statusFilter" @change="handleStatusChange">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button :value="0">待审核</el-radio-button>
          <el-radio-button :value="1">已通过</el-radio-button>
          <el-radio-button :value="2">已拒绝</el-radio-button>
          <el-radio-button :value="3">已取消</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <!-- 预约人：管理员需要知道是谁提的申请 -->
      <el-table-column prop="user_name" label="预约人" width="110" />
      <el-table-column prop="lab_name" label="实验室" min-width="150" />
      <!-- 预约对象：约整间显示「整个实验室」，约设备显示设备名 -->
      <el-table-column label="预约对象" min-width="130">
        <template #default="{ row }">
          {{ row.equipment_name ?? '整个实验室' }}
        </template>
      </el-table-column>
      <el-table-column prop="date" label="日期" width="110" />
      <el-table-column label="时间段" width="120">
        <template #default="{ row }">{{ row.start_time }} ~ {{ row.end_time }}</template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ row.remark ?? '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusMeta[row.status as ReservationStatus].tag" size="small" effect="plain">
            {{ statusMeta[row.status as ReservationStatus].text }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="申请时间" width="165">
        <template #default="{ row }">{{ fmtTime(row.create_time) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <!-- 仅待审核状态显示通过/拒绝按钮 -->
          <template v-if="row.status === 0">
            <el-button link type="success" size="small" @click="handleReview(row, 1)">通过</el-button>
            <el-button link type="danger" size="small" @click="handleReview(row, 2)">拒绝</el-button>
          </template>
          <span v-else class="no-action">-</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页控件 -->
    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        background
        hide-on-single-page
        @current-change="handlePageChange"
      />
    </div>
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 无操作时显示的占位符颜色 */
.no-action {
  color: #c0c4cc;
}

/* 分页控件靠右放置 */
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
