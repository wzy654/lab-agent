<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Calendar, DataBoard, House, Clock } from '@element-plus/icons-vue'
import { homeApi } from '@/api/home'
import type { Booking, HomeStats } from '@/api/types'
// 全局共享的用户信息（登录时存入 localStorage，见 utils/user.ts）
import { useUser } from '@/utils/user'

const stats = ref<HomeStats>()
const recent = ref<Booking[]>([])
const loading = ref(true)

// 用户信息：头像和悬停文案用
const { userInfo } = useUser()
// 计算属性：头像显示姓名首字；拿不到用户信息时显示 ?
const initial = computed(() => userInfo.value?.name?.charAt(0) ?? '?')
// 计算属性：角色中文文案（后端 role 是 'admin' / 'student'）
const roleText = computed(() =>
  userInfo.value?.role === 'admin' ? '管理员' : userInfo.value ? '学生' : '未登录',
)

onMounted(async () => {
  try {
    const [s, bookings] = await Promise.all([
      homeApi.stats(),
      homeApi.recentBookings(3),
    ])
    stats.value = s
    recent.value = bookings
  } catch {
    // 接口未就绪或请求失败时保持空状态
  } finally {
    loading.value = false
  }
})

const statusText: Record<Booking['status'], string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已驳回',
  cancelled: '已取消',
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}
</script>

<template>
  <div class="home">
    <main class="home-main">
      <!-- 欢迎横幅：右侧预留头像位置 -->
      <section class="banner">
        <div>
          <h1>欢迎使用智能实验室预约系统</h1>
          <p>在此预约实验室、管理设备，或向 AI 助手提问。</p>
        </div>
        <!-- 右侧：按钮 + 头像，水平排列 -->
        <div class="banner-right">
          <el-button type="primary" size="large" round>
            <el-icon style="margin-right: 6px"><Calendar /></el-icon>
            立即预约
          </el-button>
          <!-- el-popover：悬浮弹层，trigger="hover" 鼠标移上去显示姓名和身份 -->
          <el-popover trigger="hover" placement="bottom-end" :width="150">
            <!-- #reference 具名插槽：弹层锚点，即鼠标悬停的目标元素 -->
            <template #reference>
              <!-- el-avatar：头像组件；无照片时显示文字（姓名首字） -->
              <el-avatar class="avatar" :size="40">{{ initial }}</el-avatar>
            </template>
            <!-- 弹层内容：姓名 + 身份 -->
            <div class="popover-name">{{ userInfo?.name ?? '未知用户' }}</div>
            <div class="popover-role">{{ roleText }}</div>
          </el-popover>
        </div>
      </section>

      <!-- 数据统计 -->
      <section v-loading="loading" class="stats">
        <div class="stat-card">
          <span class="stat-label">今日预约</span>
          <span class="stat-value">{{ stats?.today_bookings ?? '--' }}</span>
          <span class="stat-desc">较昨日 {{ (stats?.today_bookings_delta ?? 0) >= 0 ? '+' : '' }}{{ stats?.today_bookings_delta ?? '--' }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">空闲实验室</span>
          <span class="stat-value">{{ stats?.free_labs ?? '--' }}</span>
          <span class="stat-desc">共 {{ stats?.total_labs ?? '--' }} 间</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">待审核</span>
          <span class="stat-value">{{ stats?.pending_reviews ?? '--' }}</span>
          <span class="stat-desc">需尽快处理</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">本月使用率</span>
          <span class="stat-value">{{ stats ? `${stats.monthly_usage_rate}%` : '--' }}</span>
          <span class="stat-desc">实验室整体使用情况</span>
        </div>
      </section>

      <!-- 下方两栏 -->
      <section class="content">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="panel-title">
              <el-icon><Clock /></el-icon>
              <span>最近预约</span>
            </div>
          </template>
          <el-empty v-if="!loading && recent.length === 0" description="暂无预约记录" :image-size="80" />
          <div v-for="b in recent" :key="b.id" class="recent-row">
            <div class="recent-info">
              <span class="recent-lab">{{ b.lab_name }}</span>
              <span class="recent-meta">{{ b.user_name }} · {{ fmtTime(b.start_time) }}</span>
            </div>
            <el-tag
              :type="b.status === 'approved' ? 'success' : b.status === 'pending' ? 'warning' : 'danger'"
              size="small"
            >
              {{ statusText[b.status] }}
            </el-tag>
          </div>
        </el-card>

        <el-card shadow="never" class="panel">
          <template #header>
            <div class="panel-title">
              <el-icon><DataBoard /></el-icon>
              <span>快捷入口</span>
            </div>
          </template>
          <div class="shortcuts">
            <div class="shortcut" @click="$router.push('/labs')">
              <el-icon :size="20"><House /></el-icon>
              <span>实验室列表</span>
            </div>
            <div class="shortcut" @click="$router.push('/devices')">
              <el-icon :size="20"><DataBoard /></el-icon>
              <span>设备管理</span>
            </div>
            <div class="shortcut" @click="$router.push('/ai')">
              <el-icon :size="20"><Calendar /></el-icon>
              <span>AI 助手</span>
            </div>
          </div>
        </el-card>
      </section>
    </main>
  </div>
</template>

<style scoped>
.home {
  min-height: 100%;
}

.home-main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.banner {
  background: linear-gradient(120deg, #1f6feb, #34c3ff);
  border-radius: 14px;
  color: #fff;
  padding: 28px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.banner h1 {
  font-size: 22px;
  margin-bottom: 8px;
}

.banner p {
  opacity: 0.85;
  font-size: 14px;
}

/* 横幅右侧：按钮 + 头像水平排列 */
.banner-right {
  display: flex;
  align-items: center;
  gap: 20px; /* 按钮与头像的间距 */
}

/* 文字头像：白底蓝字，在蓝色渐变横幅上更醒目 */
.avatar {
  background-color: #fff;
  color: #1f6feb;
  font-weight: 600;
  cursor: default; /* 纯展示，不显示手型 */
  flex-shrink: 0; /* 不允许被压缩 */
}

/* 悬停弹层里的姓名行 */
.popover-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
  text-align: center;
  margin-bottom: 4px;
}

/* 悬停弹层里的身份行 */
.popover-role {
  font-size: 12px;
  color: #909399;
  text-align: center;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border: 1px solid #e8ebee;
}

.stat-label {
  font-size: 13px;
  color: #8492a6;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2d3d;
}

.stat-desc {
  font-size: 12px;
  color: #a0aec0;
}

.content {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 16px;
}

.panel {
  border-radius: 12px;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.recent-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px dashed #edf0f3;
}

.recent-row:last-child {
  border-bottom: none;
}

.recent-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.recent-lab {
  font-weight: 500;
  color: #1f2d3d;
}

.recent-meta {
  font-size: 12px;
  color: #8492a6;
}

.shortcuts {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.shortcut {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 10px;
  background: #f4f6f8;
  cursor: pointer;
  transition: background 0.2s;
}

.shortcut:hover {
  background: #e8f1fd;
  color: #1f6feb;
}
</style>
