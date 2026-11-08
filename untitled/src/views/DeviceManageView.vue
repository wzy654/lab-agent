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
import { deviceApi } from '@/api/devices'
import { labApi } from '@/api/labs'
import { fileApi } from '@/api/files'
import { fileUrl } from '@/utils/request'
import type { DeviceInfo, LabInfo, UploadResult } from '@/api/types'

const devices = ref<DeviceInfo[]>([])
const loading = ref(true)

// ---------- 分页与搜索状态 ----------
const keyword = ref('')      // 搜索框输入的设备名称关键词
const filterLabId = ref<number | undefined>(undefined) // 按实验室过滤（undefined = 全部）
const page = ref(1)          // 当前页码（从 1 开始）
const pageSize = ref(10)     // 每页条数
const total = ref(0)         // 满足条件的总条数（由后端返回，驱动分页控件）

// 实验室下拉框的选项：新增/编辑表单和搜索过滤共用这一份
const labOptions = ref<LabInfo[]>([])

// 加载实验室下拉选项：调实验室列表接口取前 100 个（管理端实验室数量有限，够用）
// 失败静默处理：下拉框为空不影响设备列表的其他功能
async function loadLabOptions() {
  try {
    const result = await labApi.page(1, 100)
    labOptions.value = result.list
  } catch {
    // 静默：实验室选项加载失败不弹错，避免和设备列表的错误提示叠在一起
  }
}

// 加载设备列表：翻页、搜索、切换实验室过滤、增删改后的刷新都走这一个函数
async function loadDevices() {
  loading.value = true
  try {
    // page() 对应 GET /equipment/list?page=&page_size=&name=&lab_id=（需管理员 token）
    const result = await deviceApi.page(page.value, pageSize.value, keyword.value, filterLabId.value)
    devices.value = result.list
    total.value = result.total
  } catch (e) {
    // 失败必须提示（非管理员会收到后端的权限错误信息）
    ElMessage.error(e instanceof Error ? e.message : '设备列表加载失败')
  } finally {
    loading.value = false
  }
}

// 点击搜索：从第 1 页开始查（结果变少后原页码可能超出范围）
function handleSearch() {
  page.value = 1
  loadDevices()
}

// 清空搜索框时自动刷新列表
function handleSearchClear() {
  keyword.value = ''
  handleSearch()
}

// 切换实验室过滤下拉框：从第 1 页开始查
function handleLabFilterChange() {
  page.value = 1
  loadDevices()
}

// el-pagination 的页码变化回调：current-change 拿到新页码，重新查询
function handlePageChange(newPage: number) {
  page.value = newPage
  loadDevices()
}

// 启用/禁用设备：row.status 为 1 时按钮显示「禁用」，为 0 时显示「启用」
async function handleToggleStatus(row: DeviceInfo) {
  // 目标状态：当前是启用（1）就要改成禁用（0），反之亦然
  const targetStatus = row.status === 1 ? 0 : 1
  const actionText = targetStatus === 0 ? '禁用' : '启用'
  try {
    // ElMessageBox.confirm：确认弹窗，点「确定」才继续，点「取消」会抛异常
    await ElMessageBox.confirm(
      `确定要${actionText}设备「${row.name}」吗？${targetStatus === 0 ? '禁用后用户将无法预约该设备。' : ''}`,
      `确认${actionText}`,
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return // 用户点了取消，直接结束
  }
  try {
    // 调用后端接口：PUT /equipment/admin/status（需管理员 token）
    await deviceApi.setStatus(row.id, targetStatus)
    ElMessage.success(`${actionText}成功`)
    loadDevices() // 刷新列表，显示最新状态
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : `${actionText}失败，请稍后重试`)
  }
}

// 删除设备
async function handleDelete(row: DeviceInfo) {
  try {
    // 删除是不可恢复操作，确认弹窗标红提醒
    await ElMessageBox.confirm(
      `确定要删除设备「${row.name}」吗？删除后不可恢复。`,
      '确认删除',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'error' },
    )
  } catch {
    return // 用户点了取消
  }
  try {
    // 调用后端接口：DELETE /equipment/{id}（需管理员 token）
    await deviceApi.remove(row.id)
    ElMessage.success('删除成功')
    loadDevices()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '删除失败，请稍后重试')
  }
}

// ---------- 图片上传（新增/编辑弹窗共用一套逻辑） ----------
// 校验并上传图片：先检查类型和大小，再调文件接口拿相对路径
// 成功后把路径写入 form.img；formType 只用于提示文案区分（'add' | 'edit'）
async function uploadDeviceImg(file: File, setImg: (url: string) => void) {
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('只能上传图片文件')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('图片不能超过 5MB')
    return
  }
  try {
    // 把图片传给文件接口，拿到相对路径（如 uploads/xxx.png）
    const result: UploadResult = await fileApi.uploadFile(file)
    setImg(result.url)
    ElMessage.success('图片上传成功')
  } catch (e) {
    // 失败必须提示（如「文件类型不允许」「文件过大」），不能静默吞掉
    ElMessage.error(e instanceof Error ? e.message : '图片上传失败')
  }
}

// ---------- 新增设备弹窗 ----------
const addDialogVisible = ref(false) // 弹窗是否显示
const addSubmitting = ref(false)    // 提交按钮转圈状态，防止连点重复提交
const addImgUploading = ref(false)  // 图片上传中的状态
// ref 指向模板里的 <el-form ref="addFormRef">，拿到表单实例后可调用 validate() 等方法
const addFormRef = ref<FormInstance>()

// 表单的初始值工厂：每次打开弹窗都恢复到这个空状态
function defaultAddForm() {
  return {
    lab_id: undefined as number | undefined, // 所属实验室（必选），undefined 表示未选
    name: '',       // 设备名称
    quantity: 1,    // 数量（台），默认 1
    spec: '',       // 型号规格（选填）
    description: '',// 说明（选填）
    img: '',        // 图片的相对路径（选填），空字符串表示未上传
  }
}

const addForm = reactive(defaultAddForm())

// 新增表单的校验规则
const addRules: FormRules = {
  // 所属实验室必选（设备必须挂在某个实验室下）
  lab_id: [{ required: true, message: '请选择所属实验室', trigger: 'change' }],
  // 名称必填
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  // 数量必填，至少 1（el-input-number 已限制范围，这里兜底）
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
}

// 点击「新增设备」按钮：清空旧表单、清除残留校验提示，再打开弹窗
function openAddDialog() {
  Object.assign(addForm, defaultAddForm())
  addDialogVisible.value = true
  // ?. 可选链：弹窗刚打开时表单可能还没挂载，直接调用会报错
  addFormRef.value?.clearValidate()
}

// 新增弹窗上传图片（el-upload 的 :http-request 回调）
async function handleAddImgUpload(option: { file: File }) {
  addImgUploading.value = true
  // uploadDeviceImg 内部已包含校验和错误提示
  await uploadDeviceImg(option.file, (url) => { addForm.img = url })
  addImgUploading.value = false
}

// 新增弹窗里移除已选图片：只清掉表单里暂存的路径
function handleAddImgRemove() {
  addForm.img = ''
}

// 提交新增设备
async function handleAddSubmit() {
  // validate() 校验整个表单，不通过时把异常转为 false，停止提交
  const valid = await addFormRef.value?.validate().catch(() => false)
  if (!valid) return

  addSubmitting.value = true
  try {
    // 调用后端接口：POST /equipment/add（需管理员 token）
    // 空字符串的选填字段不传，避免后端存入空串而不是 null
    await deviceApi.create({
      lab_id: addForm.lab_id!,
      name: addForm.name,
      quantity: addForm.quantity,
      ...(addForm.spec ? { spec: addForm.spec } : {}),
      ...(addForm.description ? { description: addForm.description } : {}),
      // 图片路径：上传成功后才随表单一起提交
      ...(addForm.img ? { img: addForm.img } : {}),
    })
    ElMessage.success('新增设备成功')
    addDialogVisible.value = false
    // 新设备按 id 倒序排在最前面，所以回到第 1 页刷新列表
    page.value = 1
    loadDevices()
  } catch (err) {
    // 后端返回的「所属实验室不存在」等业务错误会在这里被捕获并显示
    ElMessage.error(err instanceof Error ? err.message : '新增失败，请稍后重试')
  } finally {
    addSubmitting.value = false
  }
}

// ---------- 编辑设备弹窗 ----------
const editDialogVisible = ref(false)
const editSubmitting = ref(false)
const editImgUploading = ref(false)
// 是否被用户主动清掉了图片：清掉后提交时要显式传 img: null 通知后端置空
// （后端约定「没传的字段保持原值」，所以「不传」和「传 null 清空」是两种不同操作）
const editImgRemoved = ref(false)
const editFormRef = ref<FormInstance>()

// 编辑表单的初始值工厂
function defaultEditForm() {
  return {
    id: 0,        // 要编辑的设备 id（定位用，不显示在表单里）
    lab_id: undefined as number | undefined,
    name: '',
    quantity: 1,
    spec: '',
    description: '',
    img: '',      // 当前图片的相对路径，空字符串表示没有图片
  }
}

const editForm = reactive(defaultEditForm())

// 编辑表单的校验规则：实验室、名称必填，其余选填（没填的字段不会提交）
const editRules: FormRules = {
  lab_id: [{ required: true, message: '请选择所属实验室', trigger: 'change' }],
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
}

// 点击「编辑」按钮：把该行的数据回填进表单，再打开弹窗
function openEditDialog(row: DeviceInfo) {
  // ?? 空值合并：后端 spec/description/img 可能是 null，为 null 时显示空字符串
  Object.assign(editForm, {
    id: row.id,
    lab_id: row.lab_id,
    name: row.name,
    quantity: row.quantity,
    spec: row.spec ?? '',
    description: row.description ?? '',
    img: row.img ?? '',
  })
  editDialogVisible.value = true
  // 重置「已移除图片」标记，避免上一次打开的残留状态影响这次提交
  editImgRemoved.value = false
  editFormRef.value?.clearValidate()
}

// 编辑弹窗上传图片
async function handleEditImgUpload(option: { file: File }) {
  editImgUploading.value = true
  await uploadDeviceImg(option.file, (url) => {
    editForm.img = url
    editImgRemoved.value = false // 重新上传后就不算「已移除」了
  })
  editImgUploading.value = false
}

// 编辑弹窗里移除图片：只清表单里的路径并打上「已移除」标记，点保存才真正通知后端
function handleEditImgRemove() {
  editForm.img = ''
  editImgRemoved.value = true
}

// 提交编辑设备
async function handleEditSubmit() {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return

  editSubmitting.value = true
  try {
    // 组装请求参数：必填字段总是提交；选填项留空就不传（保持数据库原值）
    const payload: Parameters<typeof deviceApi.update>[0] = {
      id: editForm.id,
      lab_id: editForm.lab_id!,
      name: editForm.name,
      quantity: editForm.quantity,
    }
    if (editForm.spec) payload.spec = editForm.spec
    if (editForm.description) payload.description = editForm.description
    // 图片的三种情况：换了新图传新路径；点了移除传 null 显式清空；没动就不传（保持原值）
    if (editImgRemoved.value) {
      payload.img = null
    } else if (editForm.img) {
      payload.img = editForm.img
    }
    // 调用后端接口：PUT /equipment/admin/update（需管理员 token）
    await deviceApi.update(payload)
    ElMessage.success('设备更新成功')
    editDialogVisible.value = false
    loadDevices()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '更新失败，请稍后重试')
  } finally {
    editSubmitting.value = false
  }
}

// 首屏加载：实验室下拉选项和设备列表并行请求
onMounted(() => {
  loadLabOptions()
  loadDevices()
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2>设备管理</h2>
      <div class="header-actions">
        <!-- 按实验室过滤：clearable 可清空（清空后 value 变 undefined 即查全部） -->
        <el-select
          v-model="filterLabId"
          placeholder="按实验室过滤"
          clearable
          style="width: 180px"
          @change="handleLabFilterChange"
        >
          <el-option
            v-for="lab in labOptions"
            :key="lab.id"
            :label="lab.name"
            :value="lab.id"
          />
        </el-select>
        <!-- @keyup.enter：按回车也能触发搜索；@clear：点叉号清空后自动刷新 -->
        <el-input
          v-model="keyword"
          placeholder="按名称搜索"
          clearable
          style="width: 200px"
          @keyup.enter="handleSearch"
          @clear="handleSearchClear"
        >
          <template #append>
            <el-button :icon="Search" @click="handleSearch" />
          </template>
        </el-input>
        <!-- 点击「新增设备」：清空旧表单并打开弹窗 -->
        <el-button type="primary" @click="openAddDialog">新增设备</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="devices" style="width: 100%">
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
            class="device-thumb"
          />
          <div v-else class="device-thumb device-thumb-empty">无图</div>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="设备名称" min-width="150" />
      <el-table-column prop="lab_name" label="所属实验室" min-width="140" />
      <el-table-column prop="spec" label="型号规格" min-width="120" />
      <el-table-column prop="quantity" label="数量(台)" width="90" />
      <el-table-column prop="description" label="说明" min-width="160" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small" effect="plain">
            {{ row.status === 1 ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <!-- { row } 解构：拿到当前行数据，按钮事件需要知道操作的是哪个设备 -->
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
          <!-- 按钮文字随状态变化：启用中显示「禁用」（红），已禁用显示「启用」（绿） -->
          <el-button
            v-if="row.status === 1"
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

    <!-- 新增设备弹窗 -->
    <el-dialog
      v-model="addDialogVisible"
      title="新增设备"
      width="460px"
      :close-on-click-modal="false"
    >
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="90px">
        <el-form-item label="所属实验室" prop="lab_id">
          <!-- el-select 下拉框：v-model 绑定选中的实验室 id，选项来自 labOptions -->
          <el-select v-model="addForm.lab_id" placeholder="请选择实验室" style="width: 100%">
            <el-option
              v-for="lab in labOptions"
              :key="lab.id"
              :label="lab.name"
              :value="lab.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="addForm.name" placeholder="如：示波器" />
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <!-- el-input-number 数字输入框：min/max 限制范围，输入框右侧带加减按钮 -->
          <el-input-number v-model="addForm.quantity" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="型号规格" prop="spec">
          <el-input v-model="addForm.spec" placeholder="选填，如：DS1054Z" />
        </el-form-item>
        <el-form-item label="说明" prop="description">
          <el-input v-model="addForm.description" type="textarea" :rows="3" placeholder="选填，设备说明" />
        </el-form-item>
        <el-form-item label="设备图片">
          <div class="img-upload-box">
            <!-- el-upload：show-file-list 关掉默认列表，用我们自己的缩略图回显 -->
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
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <!-- :loading 提交中显示转圈并禁用，防止重复提交 -->
        <el-button type="primary" :loading="addSubmitting" @click="handleAddSubmit">
          确认新增
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑设备弹窗：字段与新增相同，id 提交时自动携带 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑设备"
      width="460px"
      :close-on-click-modal="false"
    >
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="90px">
        <el-form-item label="所属实验室" prop="lab_id">
          <el-select v-model="editForm.lab_id" placeholder="请选择实验室" style="width: 100%">
            <el-option
              v-for="lab in labOptions"
              :key="lab.id"
              :label="lab.name"
              :value="lab.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="editForm.quantity" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="型号规格" prop="spec">
          <el-input v-model="editForm.spec" placeholder="选填" />
        </el-form-item>
        <el-form-item label="说明" prop="description">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="选填" />
        </el-form-item>
        <el-form-item label="设备图片">
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

/* 右上角操作区：过滤下拉框、搜索框和按钮水平排列 */
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

/* 表格里的设备缩略图 */
.device-thumb {
  width: 56px;
  height: 40px;
  border-radius: 4px;
  display: block;
}

/* 无图时的灰色占位块 */
.device-thumb-empty {
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
