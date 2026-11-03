<script setup lang="ts">
import { onMounted, ref, useTemplateRef } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { userApi } from '@/api/users'
import type { UserInfo } from '@/api/types'

const users = ref<UserInfo[]>([])
const loading = ref(true)

// ---------- 分页与搜索状态 ----------
const keyword = ref('')        // 搜索框输入的姓名关键词
const page = ref(1)            // 当前页码（从 1 开始）
const pageSize = ref(10)       // 每页条数
const total = ref(0)           // 满足条件的总条数（由后端返回，驱动分页控件）
const searchInput = useTemplateRef('searchInput') // 搜索框实例（清空用）

const roleText: Record<UserInfo['role'], string> = {
  admin: '管理员',
  student: '学生',
}

// 加载用户列表：翻页、搜索、首屏都走这一个函数
async function loadUsers() {
  loading.value = true
  try {
    // page() 对应 GET /user/list?page=&page_size=&username=（需管理员 token）
    const result = await userApi.page(page.value, pageSize.value, keyword.value)
    users.value = result.list
    total.value = result.total
  } catch (e) {
    // 失败必须提示（非管理员会收到后端的权限错误信息）
    ElMessage.error(e instanceof Error ? e.message : '用户列表加载失败')
  } finally {
    loading.value = false
  }
}

// 点击搜索：从第 1 页开始查（结果变少后原页码可能超出范围）
function handleSearch() {
  page.value = 1
  loadUsers()
}

// 清空搜索框时自动恢复全量列表
function handleSearchClear() {
  keyword.value = ''
  handleSearch()
}

// el-pagination 的页码变化回调：current-change 拿到新页码，重新查询
function handlePageChange(newPage: number) {
  page.value = newPage
  loadUsers()
}

// 首屏加载
onMounted(loadUsers)

// TODO: 新增/编辑/禁用接入 userApi.create / update / remove
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2>用户管理</h2>
      <div class="header-actions">
        <!-- @keyup.enter：按回车也能触发搜索 -->
        <el-input
          ref="searchInput"
          v-model="keyword"
          placeholder="按姓名搜索"
          clearable
          style="width: 220px"
          @keyup.enter="handleSearch"
          @clear="handleSearchClear"
        >
          <template #append>
            <el-button :icon="Search" @click="handleSearch" />
          </template>
        </el-input>
        <el-button type="primary">新增用户</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="users" style="width: 100%">
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="user_name" label="学号 / 工号" width="140" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small" effect="plain">
            {{ roleText[row.role as UserInfo['role']] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="160" />
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '1' ? 'success' : 'info'" size="small" effect="plain">
            {{ row.status === '1' ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default>
          <el-button link type="primary" size="small">编辑</el-button>
          <el-button link type="danger" size="small">禁用</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无数据" :image-size="80" />
      </template>
    </el-table>

    <!-- 分页控件：total 驱动总页数；翻页触发 handlePageChange 重新查询 -->
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

/* 右上角操作区：搜索框和按钮水平排列 */
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 分页控件靠右放置 */
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
