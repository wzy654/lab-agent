<script setup lang="ts">
// <script setup>：Vue 3 组合式 API 的语法糖，
// 里面定义的变量/函数在 <template> 模板中可以直接使用，无需 return

// reactive：把一个对象变成响应式，适合「新增用户表单」这种多字段的数据
// ref：适合单个值的响应式（这里用于弹窗开关、加载状态等布尔开关）
import { onMounted, reactive, ref, useTemplateRef } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// FormInstance：表单实例的类型；FormRules：校验规则的类型（仅类型，无运行时代码）
import type { FormInstance, FormRules } from 'element-plus'
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

// 新增用户弹窗里「角色」下拉框的选项
// value 是发给后端的值（与后端 role 字段约定一致），label 是界面显示的文字
const roleOptions = [
  { value: 'student', label: '学生' },
  { value: 'admin', label: '管理员' },
]

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

// ---------- 新增用户弹窗 ----------
// 弹窗是否显示：v-model 绑定到 el-dialog
const addDialogVisible = ref(false)
// 提交按钮的转圈状态，防止连点造成重复提交
const addSubmitting = ref(false)
// ref 指向模板里的 <el-form ref="addFormRef">，拿到表单实例后可调用 validate() 等方法
const addFormRef = ref<FormInstance>()

// 表单的初始值工厂：每次打开弹窗都调用一次，返回一个全新的空表单
// 用函数而不是直接写死，是为了「重置」时能一键恢复到这个初始状态
function defaultAddForm() {
  return {
    user_name: '',                      // 学号/工号（后端字段叫 user_name）
    name: '',                           // 姓名
    role: 'student' as UserInfo['role'],// 角色：默认新增学生
    password: '',                       // 初始密码
    confirmPassword: '',                // 确认密码：纯前端校验用，不会发给后端
  }
}

// reactive 定义表单数据，v-model 双向绑定到弹窗里的输入框
const addForm = reactive(defaultAddForm())

// 新增用户表单的校验规则（写法与登录页一致）
const addRules: FormRules = {
  // 账号必填（后端数据库已加唯一约束，重复账号会由后端报错提示）
  user_name: [{ required: true, message: '请输入学号 / 工号', trigger: 'blur' }],
  // 姓名必填（后端 AddUserRequest 的 name 是必传字段）
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  // 角色必选（虽然给了默认值，仍保留校验兜底）
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  // 密码必填且至少 6 位（与注册页的密码规则保持一致）
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  // 确认密码：validator 是自定义校验，value 是当前输入框的值
  // callback() 无参调用表示校验通过，传 Error 表示校验失败
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value: string, callback) => {
        if (value !== addForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 点击「新增用户」按钮：先清空上次填写的内容和校验提示，再打开弹窗
function openAddDialog() {
  // Object.assign：把空表单的字段逐一覆盖回 addForm，实现「重置」
  Object.assign(addForm, defaultAddForm())
  addDialogVisible.value = true
  // nextTick 时机问题：弹窗刚打开时表单可能还没挂载，这里用可选链安全调用
  // clearValidate：清除上一次打开时残留的红色校验提示
  addFormRef.value?.clearValidate()
}

// 提交新增用户
async function handleAddSubmit() {
  // validate() 校验整个表单，通过返回 true，不通过抛异常
  // .catch(() => false)：校验不通过时把异常转为 false，避免控制台报错
  const valid = await addFormRef.value?.validate().catch(() => false)
  if (!valid) return // 校验不通过，停止提交

  addSubmitting.value = true
  try {
    // 调用后端接口：POST /user/add（需管理员 token）
    // 确认密码只在前端校验，不发送给后端
    await userApi.create({
      user_name: addForm.user_name,
      name: addForm.name,
      role: addForm.role,
      password: addForm.password,
    })
    ElMessage.success('新增用户成功')
    addDialogVisible.value = false // 关闭弹窗
    // 新用户按 id 倒序排在最前面，所以回到第 1 页刷新列表
    page.value = 1
    loadUsers()
  } catch (err) {
    // 后端返回的「账号已存在」等业务错误会在这里被捕获并显示
    ElMessage.error(err instanceof Error ? err.message : '新增用户失败，请稍后重试')
  } finally {
    // finally：无论成功失败都执行，恢复按钮状态
    addSubmitting.value = false
  }
}

// 首屏加载
onMounted(loadUsers)

// ---------- 编辑用户弹窗 ----------
// 弹窗是否显示
const editDialogVisible = ref(false)
// 提交按钮的转圈状态，防止连点造成重复提交
const editSubmitting = ref(false)
// ref 指向模板里的 <el-form ref="editFormRef">，拿到表单实例后可调用 validate() 等方法
const editFormRef = ref<FormInstance>()

// 编辑表单的初始值工厂：每次打开弹窗都恢复到这个空状态
function defaultEditForm() {
  return {
    user_name: '',                        // 学号/工号：只用于定位用户，不可修改
    name: '',                             // 姓名
    role: 'student' as UserInfo['role'],  // 角色
    email: '',                            // 邮箱（选填）
    phone: '',                            // 手机号（选填）
  }
}

// reactive 定义编辑表单数据
const editForm = reactive(defaultEditForm())

// 编辑表单的校验规则
const editRules: FormRules = {
  // 姓名必填（与新增、个人信息修改的规则一致）
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  // 邮箱选填：type: 'email' 只在填了内容时才校验格式，空值会自动跳过
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  // 手机号选填：pattern 是正则校验，1 开头共 11 位数字
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }],
}

// 点击「编辑」按钮：把该行的数据回填进表单，再打开弹窗
function openEditDialog(row: UserInfo) {
  // ?? 空值合并：后端 email/phone 可能是 null，为 null 时显示空字符串
  Object.assign(editForm, {
    user_name: row.user_name,
    name: row.name,
    role: row.role,
    email: row.email ?? '',
    phone: row.phone ?? '',
  })
  editDialogVisible.value = true
  // 清除上一次打开时残留的红色校验提示（?. 可选链防表单未挂载时报错）
  editFormRef.value?.clearValidate()
}

// 提交编辑用户
async function handleEditSubmit() {
  // validate() 校验整个表单，不通过时把异常转为 false，停止提交
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return

  editSubmitting.value = true
  try {
    // 组装请求参数：只提交有内容的字段
    // 后端约定「没传的字段保持原值」，所以邮箱/手机号留空就不传，避免清空数据库原有值
    const payload: Parameters<typeof userApi.update>[0] = {
      user_name: editForm.user_name,
      name: editForm.name,
      role: editForm.role,
    }
    if (editForm.email) payload.email = editForm.email
    if (editForm.phone) payload.phone = editForm.phone
    // 调用后端接口：PUT /user/admin/update（需管理员 token）
    await userApi.update(payload)
    ElMessage.success('用户信息更新成功')
    editDialogVisible.value = false // 关闭弹窗
    loadUsers() // 刷新列表，显示最新数据
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '更新失败，请稍后重试')
  } finally {
    // finally：无论成功失败都执行，恢复按钮状态
    editSubmitting.value = false
  }
}

// 启用/禁用用户：row.status 为 '1' 时按钮显示「禁用」，为 '0' 时显示「启用」
async function handleToggleStatus(row: UserInfo) {
  // 目标状态：当前是启用（'1'）就要改成禁用（'0'），反之亦然
  const targetStatus = row.status === '1' ? '0' : '1'
  const actionText = targetStatus === '0' ? '禁用' : '启用'
  try {
    // ElMessageBox.confirm：确认弹窗，用户点「确定」才继续往下走，点「取消」会抛异常
    await ElMessageBox.confirm(
      `确定要${actionText}用户「${row.name}」吗？${targetStatus === '0' ? '禁用后该用户将无法登录。' : ''}`,
      `确认${actionText}`,
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return // 用户点了取消，直接结束
  }
  try {
    // 调用后端接口：PUT /user/admin/status（需管理员 token）
    await userApi.setStatus(row.user_name, targetStatus)
    ElMessage.success(`${actionText}成功`)
    loadUsers() // 刷新列表，显示最新状态
  } catch (err) {
    // 后端返回的「不能禁用当前登录的管理员账号」等业务错误会在这里显示
    ElMessage.error(err instanceof Error ? err.message : `${actionText}失败，请稍后重试`)
  }
}

// TODO: 删除接入 userApi.remove
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
        <!-- 点击「新增用户」：清空旧表单并打开弹窗 -->
        <el-button type="primary" @click="openAddDialog">新增用户</el-button>
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
        <!-- { row } 解构：拿到当前行数据，按钮事件需要知道操作的是哪个用户 -->
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
          <!-- 按钮文字随状态变化：启用中显示「禁用」（红），已禁用显示「启用」（绿） -->
          <el-button
            v-if="row.status === '1'"
            link
            type="danger"
            size="small"
            @click="handleToggleStatus(row)"
          >禁用</el-button>
          <el-button
            v-else
            link
            type="success"
            size="small"
            @click="handleToggleStatus(row)"
          >启用</el-button>
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

    <!-- 新增用户弹窗：el-dialog 是 Element Plus 的模态对话框 -->
    <!-- v-model 控制显示/隐藏；width 设置宽度；:close-on-click-modal 禁止点遮罩误关 -->
    <el-dialog
      v-model="addDialogVisible"
      title="新增用户"
      width="440px"
      :close-on-click-modal="false"
    >
      <!-- 弹窗内的表单：:model 绑定数据、:rules 绑定校验规则、label-width 统一标签宽度 -->
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="90px">
        <!-- prop 必须与 addRules 里的键同名，校验才能找到对应的输入框 -->
        <el-form-item label="学号 / 工号" prop="user_name">
          <el-input v-model="addForm.user_name" placeholder="登录用的账号，创建后不可修改" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="addForm.name" placeholder="用户真实姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <!-- el-select 下拉框：v-model 绑定选中的 value，选项由 roleOptions 提供 -->
          <el-select v-model="addForm.role" style="width: 100%">
            <el-option
              v-for="opt in roleOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <!-- show-password：显示「小眼睛」切换明文/密文 -->
          <el-input v-model="addForm.password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="addForm.confirmPassword"
            type="password"
            show-password
            placeholder="再输入一遍密码"
          />
        </el-form-item>
      </el-form>
      <!-- 自定义弹窗底部按钮区：#footer 是 el-dialog 的具名插槽 -->
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <!-- :loading 提交中显示转圈并禁用，防止重复提交 -->
        <el-button type="primary" :loading="addSubmitting" @click="handleAddSubmit">
          确认新增
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户弹窗：结构与新增弹窗类似，多一个只读账号展示 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑用户"
      width="440px"
      :close-on-click-modal="false"
    >
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="90px">
        <!-- 账号只读展示：disabled 输入框灰显，仅用于告知管理员正在编辑谁 -->
        <el-form-item label="学号 / 工号">
          <el-input :model-value="editForm.user_name" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="editForm.name" placeholder="用户真实姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="editForm.role" style="width: 100%">
            <el-option
              v-for="opt in roleOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="选填，格式需为邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editForm.phone" placeholder="选填，1 开头的 11 位号码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSubmitting" @click="handleEditSubmit">
          保存修改
        </el-button>
      </template>
    </el-dialog>
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
