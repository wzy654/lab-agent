<script setup lang="ts">
// <script setup>：Vue 3 组合式 API 的语法糖，
// 里面定义的变量/函数在 <template> 模板中可以直接使用，无需 return

// reactive：把对象变成响应式，适合「新增/编辑表单」这种多字段的数据
// ref：适合单个值的响应式（弹窗开关、加载状态等布尔开关）
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// FormInstance：表单实例的类型；FormRules：校验规则的类型（仅类型，无运行时代码）
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { labApi } from '@/api/labs'
import { fileApi } from '@/api/files'
import { fileUrl } from '@/utils/request'
import type { LabInfo, UploadResult } from '@/api/types'

const labs = ref<LabInfo[]>([])
const loading = ref(true)

// ---------- 分页与搜索状态 ----------
const keyword = ref('')   // 搜索框输入的实验室名称关键词
const page = ref(1)       // 当前页码（从 1 开始）
const pageSize = ref(10)  // 每页条数
const total = ref(0)      // 满足条件的总条数（由后端返回，驱动分页控件）

// 加载实验室列表：翻页、搜索、首屏、增删改后的刷新都走这一个函数
async function loadLabs() {
  loading.value = true
  try {
    // page() 对应 GET /lab/list?page=&page_size=&name=（需管理员 token）
    const result = await labApi.page(page.value, pageSize.value, keyword.value)
    labs.value = result.list
    total.value = result.total
  } catch (e) {
    // 失败必须提示（非管理员会收到后端的权限错误信息）
    ElMessage.error(e instanceof Error ? e.message : '实验室列表加载失败')
  } finally {
    loading.value = false
  }
}

// 点击搜索：从第 1 页开始查（结果变少后原页码可能超出范围）
function handleSearch() {
  page.value = 1
  loadLabs()
}

// 清空搜索框时自动恢复全量列表
function handleSearchClear() {
  keyword.value = ''
  handleSearch()
}

// el-pagination 的页码变化回调：current-change 拿到新页码，重新查询
function handlePageChange(newPage: number) {
  page.value = newPage
  loadLabs()
}

// 启用/禁用实验室：row.status 为 '1' 时按钮显示「禁用」，为 '0' 时显示「启用」
async function handleToggleStatus(row: LabInfo) {
  // 目标状态：当前是启用（'1'）就要改成禁用（'0'），反之亦然
  const targetStatus = row.status === '1' ? '0' : '1'
  const actionText = targetStatus === '0' ? '禁用' : '启用'
  try {
    // ElMessageBox.confirm：确认弹窗，点「确定」才继续，点「取消」会抛异常
    await ElMessageBox.confirm(
      `确定要${actionText}实验室「${row.name}」吗？${targetStatus === '0' ? '禁用后用户将无法预约该实验室。' : ''}`,
      `确认${actionText}`,
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return // 用户点了取消，直接结束
  }
  try {
    // 调用后端接口：PUT /lab/admin/status（需管理员 token）
    await labApi.setStatus(row.id, targetStatus)
    ElMessage.success(`${actionText}成功`)
    loadLabs() // 刷新列表，显示最新状态
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : `${actionText}失败，请稍后重试`)
  }
}

// 删除实验室
async function handleDelete(row: LabInfo) {
  try {
    // 删除是不可恢复操作，确认弹窗标红提醒
    await ElMessageBox.confirm(
      `确定要删除实验室「${row.name}」吗？删除后不可恢复。`,
      '确认删除',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'error' },
    )
  } catch {
    return // 用户点了取消
  }
  try {
    // 调用后端接口：DELETE /lab/{id}（需管理员 token）
    await labApi.remove(row.id)
    ElMessage.success('删除成功')
    loadLabs()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '删除失败，请稍后重试')
  }
}

// ---------- 新增实验室弹窗 ----------
const addDialogVisible = ref(false) // 弹窗是否显示
const addSubmitting = ref(false)    // 提交按钮转圈状态，防止连点重复提交
// ref 指向模板里的 <el-form ref="addFormRef">，拿到表单实例后可调用 validate() 等方法
const addFormRef = ref<FormInstance>()

// 表单的初始值工厂：每次打开弹窗都恢复到这个空状态
function defaultAddForm() {
  return {
    name: '',           // 实验室名称
    location: '',       // 位置（选填）
    capacity: 30,       // 容量（人），给个常见默认值
    open_time: '08:00', // 开放时间（必填）
    close_time: '22:00',// 关闭时间（必填）
    description: '',    // 简介（选填）
    img: '',            // 封面图片的相对路径（选填），空字符串表示未上传
  }
}

// reactive 定义表单数据，v-model 双向绑定到弹窗里的输入框
const addForm = reactive(defaultAddForm())
// 图片上传中的转圈状态
const addImgUploading = ref(false)

// 上传实验室封面图：el-upload 选中图片后立刻走这里（:http-request 接管默认上传行为）
// 流程和首页换头像一致：先传文件接口拿路径，把路径暂存到表单里，提交时随表单一起入库
async function handleAddImgUpload(option: { file: File }) {
  const file = option.file
  // 前端先做一层简单校验：只收图片、不超过 5MB（后端还有一道校验兜底）
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('只能上传图片文件')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('图片不能超过 5MB')
    return
  }
  addImgUploading.value = true
  try {
    // 把图片传给文件接口，拿到相对路径（如 uploads/xxx.png）存进表单
    const result: UploadResult = await fileApi.uploadFile(file)
    addForm.img = result.url
    ElMessage.success('图片上传成功')
  } catch (e) {
    // 失败必须提示（如「文件类型不允许」「文件过大」），不能静默吞掉
    ElMessage.error(e instanceof Error ? e.message : '图片上传失败')
  } finally {
    addImgUploading.value = false
  }
}

// 新增弹窗里移除已选图片：只清掉表单里暂存的路径，文件仍留在服务器上（不影响其他地方引用）
function handleAddImgRemove() {
  addForm.img = ''
}

// 新增表单的校验规则
const addRules: FormRules = {
  // 名称必填（后端还会查重，重名会返回「实验室名称已存在」）
  name: [{ required: true, message: '请输入实验室名称', trigger: 'blur' }],
  // 容量必填，至少 1（el-input-number 已限制范围，这里兜底）
  capacity: [{ required: true, message: '请输入容量', trigger: 'blur' }],
  open_time: [{ required: true, message: '请选择开放时间', trigger: 'change' }],
  close_time: [{ required: true, message: '请选择关闭时间', trigger: 'change' }],
}

// 点击「新增实验室」按钮：清空旧表单、清除残留校验提示，再打开弹窗
function openAddDialog() {
  // Object.assign：把空表单的字段逐一覆盖回 addForm，实现「重置」
  Object.assign(addForm, defaultAddForm())
  addDialogVisible.value = true
  // ?. 可选链：弹窗刚打开时表单可能还没挂载，直接调用会报错
  addFormRef.value?.clearValidate()
}

// 提交新增实验室
async function handleAddSubmit() {
  // validate() 校验整个表单，不通过时把异常转为 false，停止提交
  const valid = await addFormRef.value?.validate().catch(() => false)
  if (!valid) return
  // 关闭时间必须晚于开放时间（"HH:mm" 格式的字符串可以直接比较大小）
  if (addForm.close_time <= addForm.open_time) {
    ElMessage.warning('关闭时间必须晚于开放时间')
    return
  }

  addSubmitting.value = true
  try {
    // 调用后端接口：POST /lab/add（需管理员 token）
    // 空字符串的选填字段不传，避免后端存入空串而不是 null
    await labApi.create({
      name: addForm.name,
      capacity: addForm.capacity,
      open_time: addForm.open_time,
      close_time: addForm.close_time,
      ...(addForm.location ? { location: addForm.location } : {}),
      ...(addForm.description ? { description: addForm.description } : {}),
      // 图片路径：上传成功后才随表单一起提交
      ...(addForm.img ? { img: addForm.img } : {}),
    })
    ElMessage.success('新增实验室成功')
    addDialogVisible.value = false
    // 新实验室按 id 倒序排在最前面，所以回到第 1 页刷新列表
    page.value = 1
    loadLabs()
  } catch (err) {
    // 后端返回的「实验室名称已存在」等业务错误会在这里被捕获并显示
    ElMessage.error(err instanceof Error ? err.message : '新增失败，请稍后重试')
  } finally {
    addSubmitting.value = false
  }
}

// ---------- 编辑实验室弹窗 ----------
const editDialogVisible = ref(false)
const editSubmitting = ref(false)
const editFormRef = ref<FormInstance>()

// 编辑表单的初始值工厂
function defaultEditForm() {
  return {
    id: 0,              // 要编辑的实验室 id（定位用，不显示在表单里）
    name: '',
    location: '',       // 回显时后端的 null 会转成空字符串
    capacity: 0,
    open_time: '',
    close_time: '',
    description: '',
    img: '',            // 当前图片的相对路径，空字符串表示没有图片
  }
}

const editForm = reactive(defaultEditForm())
// 图片上传中的转圈状态
const editImgUploading = ref(false)
// 是否被用户主动清掉了图片：清掉后提交时要显式传 img: null 通知后端置空
// （后端约定「没传的字段保持原值」，所以「不传」和「传 null 清空」是两种不同操作）
const editImgRemoved = ref(false)

// 上传实验室封面图（编辑弹窗）：逻辑与新增弹窗一致
async function handleEditImgUpload(option: { file: File }) {
  const file = option.file
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('只能上传图片文件')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('图片不能超过 5MB')
    return
  }
  editImgUploading.value = true
  try {
    const result: UploadResult = await fileApi.uploadFile(file)
    editForm.img = result.url
    editImgRemoved.value = false // 重新上传后就不算「已移除」了
    ElMessage.success('图片上传成功')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '图片上传失败')
  } finally {
    editImgUploading.value = false
  }
}

// 编辑弹窗里移除图片：只清表单里的路径并打上「已移除」标记，点保存才真正通知后端
function handleEditImgRemove() {
  editForm.img = ''
  editImgRemoved.value = true
}

// 编辑表单的校验规则：只有名称必填，其余选填（没填的字段不会提交）
const editRules: FormRules = {
  name: [{ required: true, message: '请输入实验室名称', trigger: 'blur' }],
}

// 点击「编辑」按钮：把该行的数据回填进表单，再打开弹窗
function openEditDialog(row: LabInfo) {
  // ?? 空值合并：后端 location/description 可能是 null，为 null 时显示空字符串
  Object.assign(editForm, {
    id: row.id,
    name: row.name,
    location: row.location ?? '',
    capacity: row.capacity,
    open_time: row.open_time,
    close_time: row.close_time,
    description: row.description ?? '',
    img: row.img ?? '',
  })
  editDialogVisible.value = true
  // 重置「已移除图片」标记，避免上一次打开的残留状态影响这次提交
  editImgRemoved.value = false
  editFormRef.value?.clearValidate()
}

// 提交编辑实验室
async function handleEditSubmit() {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return
  // 如果开放/关闭时间都填了，校验先后关系
  if (editForm.open_time && editForm.close_time && editForm.close_time <= editForm.open_time) {
    ElMessage.warning('关闭时间必须晚于开放时间')
    return
  }

  editSubmitting.value = true
  try {
    // 组装请求参数：只提交有内容的字段
    // 后端约定「没传的字段保持原值」，选填项留空就不传，避免清空数据库原有值
    const payload: Parameters<typeof labApi.update>[0] = {
      id: editForm.id,
      name: editForm.name,
      capacity: editForm.capacity,
      open_time: editForm.open_time,
      close_time: editForm.close_time,
    }
    if (editForm.location) payload.location = editForm.location
    if (editForm.description) payload.description = editForm.description
    // 图片的三种情况：换了新图传新路径；点了移除传 null 显式清空；没动就不传（保持原值）
    if (editImgRemoved.value) {
      payload.img = null
    } else if (editForm.img) {
      payload.img = editForm.img
    }
    // 调用后端接口：PUT /lab/admin/update（需管理员 token）
    await labApi.update(payload)
    ElMessage.success('实验室更新成功')
    editDialogVisible.value = false
    loadLabs()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '更新失败，请稍后重试')
  } finally {
    editSubmitting.value = false
  }
}

// 首屏加载
onMounted(loadLabs)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2>实验室管理</h2>
      <div class="header-actions">
        <!-- @keyup.enter：按回车也能触发搜索；@clear：点叉号清空后自动刷新 -->
        <el-input
          v-model="keyword"
          placeholder="按名称搜索"
          clearable
          style="width: 220px"
          @keyup.enter="handleSearch"
          @clear="handleSearchClear"
        >
          <template #append>
            <el-button :icon="Search" @click="handleSearch" />
          </template>
        </el-input>
        <!-- 点击「新增实验室」：清空旧表单并打开弹窗 -->
        <el-button type="primary" @click="openAddDialog">新增实验室</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="labs" style="width: 100%">
      <!-- 不写 label 属性：这一列只有缩略图，不需要文字标题，页面更简洁 -->
      <el-table-column width="80">
        <template #default="{ row }">
          <!-- 有图显示缩略图（点击可放大预览），无图显示灰色占位 -->
          <el-image
            v-if="row.img"
            :src="fileUrl(row.img)"
            :preview-src-list="[fileUrl(row.img)]"
            preview-teleported
            fit="cover"
            class="lab-thumb"
          />
          <div v-else class="lab-thumb lab-thumb-empty">无图</div>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="实验室名称" min-width="160" />
      <el-table-column prop="location" label="位置" min-width="120" />
      <el-table-column prop="capacity" label="容量(人)" width="90" />
      <el-table-column label="开放时间" width="140">
        <!-- 同一列显示「开放 ~ 关闭」时间段，代码比拆两列更紧凑 -->
        <template #default="{ row }">
          {{ row.open_time }} ~ {{ row.close_time }}
        </template>
      </el-table-column>
      <el-table-column prop="description" label="简介" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '1' ? 'success' : 'info'" size="small" effect="plain">
            {{ row.status === '1' ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <!-- { row } 解构：拿到当前行数据，按钮事件需要知道操作的是哪个实验室 -->
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
          <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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

    <!-- 新增实验室弹窗：el-dialog 是 Element Plus 的模态对话框 -->
    <!-- v-model 控制显示/隐藏；:close-on-click-modal 禁止点遮罩误关 -->
    <el-dialog
      v-model="addDialogVisible"
      title="新增实验室"
      width="460px"
      :close-on-click-modal="false"
    >
      <!-- label-width 统一标签宽度，让输入框左对齐 -->
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="addForm.name" placeholder="实验室名称，如：软件实验室A101" />
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="addForm.location" placeholder="选填，如：第一教学楼 3 楼" />
        </el-form-item>
        <el-form-item label="容量" prop="capacity">
          <!-- el-input-number 数字输入框：min/max 限制范围，输入框右侧带加减按钮 -->
          <el-input-number v-model="addForm.capacity" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="开放时间" prop="open_time">
          <!-- el-time-picker 选时间；value-format 指定存值为 "HH:mm" 字符串，与后端格式一致 -->
          <el-time-picker v-model="addForm.open_time" value-format="HH:mm" format="HH:mm" placeholder="开放时间" />
        </el-form-item>
        <el-form-item label="关闭时间" prop="close_time">
          <el-time-picker v-model="addForm.close_time" value-format="HH:mm" format="HH:mm" placeholder="关闭时间" />
        </el-form-item>
        <el-form-item label="简介" prop="description">
          <!-- type="textarea" 多行输入；:rows 控制默认行数 -->
          <el-input v-model="addForm.description" type="textarea" :rows="3" placeholder="选填，实验室简介" />
        </el-form-item>
        <el-form-item label="封面图">
          <div class="img-upload-box">
            <!-- el-upload：show-file-list 关掉默认列表，用我们自己的缩略图回显 -->
            <!-- accept 限制选图；http-request 接管上传，走 handleAddImgUpload -->
            <el-upload
              :show-file-list="false"
              accept="image/*"
              :http-request="handleAddImgUpload"
            >
              <!-- 已上传显示缩略图（点击图片区域可重新选图替换），未上传显示「+」占位 -->
              <el-image
                v-if="addForm.img"
                :src="fileUrl(addForm.img)"
                fit="cover"
                class="img-preview"
              />
              <div v-else class="img-placeholder">
                <el-icon><Plus /></el-icon>
                <span>{{ addImgUploading ? '上传中...' : '上传图片' }}</span>
              </div>
            </el-upload>
            <!-- 只在已上传时显示移除按钮 -->
            <el-button
              v-if="addForm.img"
              link
              type="danger"
              size="small"
              @click="handleAddImgRemove"
            >移除图片</el-button>
          </div>
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

    <!-- 编辑实验室弹窗：字段与新增相同，但不显示 id（提交时自动携带） -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑实验室"
      width="460px"
      :close-on-click-modal="false"
    >
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="editForm.location" placeholder="选填" />
        </el-form-item>
        <el-form-item label="容量" prop="capacity">
          <el-input-number v-model="editForm.capacity" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="开放时间" prop="open_time">
          <el-time-picker v-model="editForm.open_time" value-format="HH:mm" format="HH:mm" />
        </el-form-item>
        <el-form-item label="关闭时间" prop="close_time">
          <el-time-picker v-model="editForm.close_time" value-format="HH:mm" format="HH:mm" />
        </el-form-item>
        <el-form-item label="简介" prop="description">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="选填" />
        </el-form-item>
        <el-form-item label="封面图">
          <div class="img-upload-box">
            <el-upload
              :show-file-list="false"
              accept="image/*"
              :http-request="handleEditImgUpload"
            >
              <el-image
                v-if="editForm.img"
                :src="fileUrl(editForm.img)"
                fit="cover"
                class="img-preview"
              />
              <div v-else class="img-placeholder">
                <el-icon><Plus /></el-icon>
                <span>{{ editImgUploading ? '上传中...' : '上传图片' }}</span>
              </div>
            </el-upload>
            <!-- 移除按钮：只标记待清空，点「保存修改」才真正通知后端置空 -->
            <el-button
              v-if="editForm.img"
              link
              type="danger"
              size="small"
              @click="handleEditImgRemove"
            >移除图片</el-button>
          </div>
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

/* 表格里的实验室封面缩略图 */
.lab-thumb {
  width: 56px;
  height: 40px;
  border-radius: 4px;
  display: block;
}

/* 无图时的灰色占位块 */
.lab-thumb-empty {
  background: #f0f2f5;
  color: #a0aec0;
  font-size: 12px;
  line-height: 40px;
  text-align: center;
}

/* 弹窗里的图片上传区 */
.img-upload-box {
  display: flex;
  flex-direction: column; /* 缩略图在上、移除按钮在下 */
  align-items: flex-start;
  gap: 4px;
}

/* 已上传图片的预览块：点击可重新选图替换 */
.img-preview {
  width: 120px;
  height: 80px;
  border-radius: 6px;
  cursor: pointer;
}

/* 未上传时的虚线占位块：点击选图 */
.img-placeholder {
  width: 120px;
  height: 80px;
  border: 1px dashed #c0c4cc;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #909399;
  font-size: 12px;
  cursor: pointer;
}

</style>
