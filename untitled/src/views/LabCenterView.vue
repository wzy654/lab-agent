<script setup lang="ts">
// <script setup>：Vue 3 组合式 API 的语法糖，
// 里面定义的变量/函数在 <template> 模板中可以直接使用，无需 return

import { computed, onMounted, reactive, ref, useTemplateRef } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { labApi } from '@/api/labs'
import { reservationApi } from '@/api/reservations'
import { fileUrl } from '@/utils/request'
import { useUser } from '@/utils/user'
import type { LabDetail, LabEquipmentItem, LabInfo } from '@/api/types'

// 当前登录用户：用来判断角色——管理员可以按状态过滤，学生只能看启用的
const { userInfo } = useUser()
// computed 计算属性：isAdmin 随 userInfo 自动更新
const isAdmin = computed(() => userInfo.value?.role === 'admin')

const labs = ref<LabInfo[]>([])
const loading = ref(true)

// ---------- 分页与搜索状态 ----------
const keyword = ref('')   // 搜索框输入的实验室名称关键词
const page = ref(1)       // 当前页码（从 1 开始）
const pageSize = ref(9)   // 每页条数：9 张卡片正好排 3 行 × 3 列
const total = ref(0)      // 满足条件的总条数（由后端返回，驱动分页控件）

// 加载实验室列表：翻页、搜索后的刷新都走这一个函数
// 不传 status：学生由后端强制只返回启用的；管理员误入此页则看到全部
async function loadLabs() {
  loading.value = true
  try {
    const result = await labApi.page(page.value, pageSize.value, keyword.value)
    labs.value = result.list
    total.value = result.total
  } catch (e) {
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

// el-pagination 的页码变化回调
function handlePageChange(newPage: number) {
  page.value = newPage
  loadLabs()
}

// ---------- 详情弹窗 ----------
const detailVisible = ref(false)       // 弹窗是否显示
const detailLoading = ref(false)       // 详情加载转圈状态
const detail = ref<LabDetail | null>() // 当前查看的实验室详情（含设备列表）

// 点击卡片「查看详情」：调详情接口拿实验室信息 + 挂载的设备
async function openDetail(row: LabInfo) {
  detailVisible.value = true
  detailLoading.value = true
  detail.value = undefined // 先清掉上一次的详情，避免弹窗闪现旧数据
  try {
    // GET /lab/{id}：后端返回实验室信息 + equipment 设备列表
    detail.value = await labApi.detail(row.id)
  } catch (e) {
    // 学生点已被禁用的实验室会收到「实验室不存在或已停用」
    ElMessage.error(e instanceof Error ? e.message : '获取实验室详情失败')
    detailVisible.value = false // 加载失败直接关弹窗
  } finally {
    detailLoading.value = false
  }
}

// ---------- 预约弹窗 ----------
// 入口有两处：卡片上的「立即预约」（默认约整个实验室）、设备列表里的「立即预约」（已选好设备）
const bookingVisible = ref(false)   // 预约弹窗显隐
const bookingSaving = ref(false)    // 提交按钮 loading，防重复提交
const bookingLoading = ref(false)   // 打开弹窗时加载实验室详情的 loading

// 本次预约的目标实验室详情（含设备列表、开放时间，供表单使用）
const bookingLab = ref<LabDetail>()

// 表单实例：用于触发整表校验
const bookingFormRef = useTemplateRef('bookingFormRef')

// 预约表单：target 记录预约对象（整间实验室 / 指定设备），提交时再换算成 equipment_id
const bookingForm = reactive({
  target: 'lab' as 'lab' | 'device',     // 'lab' 整间实验室，'device' 指定设备
  equipment_id: undefined as number | undefined, // 选中的设备 id（target 为 device 时才有值）
  date: '',        // "YYYY-MM-DD"
  start_time: '',  // "HH:mm"
  end_time: '',    // "HH:mm"
  remark: '',      // 备注选填
})

// 校验规则：日期和起止时间必填；结束时间必须晚于开始时间；选设备模式时设备必选
const bookingRules = {
  date: [{ required: true, message: '请选择预约日期', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [
    { required: true, message: '请选择结束时间', trigger: 'change' },
    {
      // 自定义校验：结束时间必须晚于开始时间
      validator: (_rule: unknown, value: string, callback: (err?: Error) => void) => {
        if (value && bookingForm.start_time && value <= bookingForm.start_time) {
          callback(new Error('结束时间必须晚于开始时间'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
  equipment_id: [
    {
      // 选「指定设备」时必须选中一台设备；整间实验室模式放行
      validator: (_rule: unknown, value: number | undefined, callback: (err?: Error) => void) => {
        if (bookingForm.target === 'device' && !value) {
          callback(new Error('请选择要预约的设备'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
}

// 可预约的设备：只展示状态为启用（1）的，禁用设备不允许约
const availableEquipments = computed(
  () => bookingLab.value?.equipment.filter((eq) => eq.status === 1) ?? [],
)

// 重置表单为初始状态（每次打开预约弹窗时调用）
function resetBookingForm() {
  bookingForm.target = 'lab'
  bookingForm.equipment_id = undefined
  bookingForm.date = ''
  bookingForm.start_time = ''
  bookingForm.end_time = ''
  bookingForm.remark = ''
}

// 打开预约弹窗：每次都重新拉取实验室详情，保证设备列表和开放时间是最新的
// lab：预约目标；presetDeviceId：从设备列表进入时直接选中的设备 id
async function openBooking(lab?: LabInfo, presetDeviceId?: number) {
  if (!lab) return // 详情还没加载完时防御一下
  resetBookingForm()
  bookingVisible.value = true
  bookingLoading.value = true
  bookingLab.value = undefined // 清掉上一次的实验室，避免闪现旧数据
  try {
    bookingLab.value = await labApi.detail(lab.id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '获取实验室信息失败')
    bookingVisible.value = false
    return
  } finally {
    bookingLoading.value = false
  }
  // 从设备列表进入：预约对象自动切到「指定设备」并选中该设备
  if (presetDeviceId) {
    bookingForm.target = 'device'
    bookingForm.equipment_id = presetDeviceId
  }
}

// 设备列表里的「立即预约」：带上设备 id 打开预约弹窗（禁用设备不可点）
function bookDevice(eq: LabEquipmentItem) {
  if (eq.status !== 1) return
  openBooking(detail.value, eq.id)
}

// 日期选择器禁用过去的日期（今天可选，具体时刻由后端校验）
function disablePastDate(d: Date) {
  const today = new Date()
  today.setHours(0, 0, 0, 0) // 今天 0 点之前都禁用
  return d.getTime() < today.getTime()
}

// 提交预约：校验通过后调 POST /reservation
async function submitBooking() {
  // 校验不通过时 validate() 会 reject，红字已显示在表单项下方
  try {
    await bookingFormRef.value?.validate()
  } catch {
    return
  }
  bookingSaving.value = true
  try {
    await reservationApi.create({
      // bookingLab 在弹窗打开时已加载完成，用 ! 断言拿到实验室 id
      lab_id: bookingLab.value!.id,
      // 整间实验室：equipment_id 传 null；指定设备：传设备 id
      equipment_id: bookingForm.target === 'device' ? bookingForm.equipment_id : null,
      date: bookingForm.date,
      start_time: bookingForm.start_time,
      end_time: bookingForm.end_time,
      remark: bookingForm.remark || undefined, // 空字符串不上传
    })
    ElMessage.success('预约提交成功，请等待审核')
    bookingVisible.value = false
  } catch (e) {
    // 失败提示（如「所选时间已被预约」「预约时间不能早于当前时间」）
    ElMessage.error(e instanceof Error ? e.message : '预约提交失败')
  } finally {
    bookingSaving.value = false
  }
}

// 首屏加载
onMounted(loadLabs)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2>实验室浏览</h2>
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
      </div>
    </div>

    <div v-loading="loading" class="lab-grid">
      <!-- 卡片网格：v-for 遍历当前页的实验室，每张卡展示封面和关键信息 -->
      <el-card
        v-for="lab in labs"
        :key="lab.id"
        shadow="hover"
        class="lab-card"
      >
        <!-- 封面图：没有图时 el-image 自带的灰色占位槽 -->
        <el-image
          :src="lab.img ? fileUrl(lab.img) : undefined"
          fit="cover"
          class="lab-cover"
        >
          <template #error>
            <div class="lab-cover-fallback">暂无图片</div>
          </template>
        </el-image>
        <div class="lab-body">
          <div class="lab-name-row">
            <span class="lab-name">{{ lab.name }}</span>
            <!-- 状态标签：仅管理员显示（学生看到的全部是启用状态，无需展示） -->
            <el-tag
              v-if="isAdmin"
              :type="lab.status === 1 ? 'success' : 'info'"
              size="small"
              effect="plain"
            >
              {{ lab.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </div>
          <div class="lab-meta">位置：{{ lab.location ?? '未填写' }}</div>
          <div class="lab-meta">容量：{{ lab.capacity }} 人</div>
          <div class="lab-meta">开放：{{ lab.open_time }} ~ {{ lab.close_time }}</div>
          <!-- 简介：超长省略，悬停 title 提示完整内容 -->
          <div class="lab-desc" :title="lab.description ?? ''">{{ lab.description ?? '暂无简介' }}</div>
          <!-- 卡片操作区：查看设备 = 打开设备列表；立即预约 = 直接预约整个实验室 -->
          <div class="lab-actions">
            <el-button type="primary" size="small" @click="openDetail(lab)">查看设备</el-button>
            <el-button size="small" @click="openBooking(lab)">立即预约</el-button>
          </div>
        </div>
      </el-card>

      <!-- 列表为空时的占位提示 -->
      <el-empty v-if="!loading && labs.length === 0" description="暂无实验室" class="grid-empty" />
    </div>

    <!-- 分页控件：翻页触发 handlePageChange 重新查询 -->
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

    <!-- 实验室详情弹窗：上半部分是实验室信息，下半部分是挂载的设备表格 -->
    <el-dialog v-model="detailVisible" :title="detail?.name ?? '实验室详情'" width="640px">
      <div v-loading="detailLoading" class="detail-body">
        <template v-if="detail">
          <!-- 封面大图 + 基本信息左右排布 -->
          <div class="detail-top">
            <el-image
              :src="detail.img ? fileUrl(detail.img) : undefined"
              fit="cover"
              class="detail-cover"
            >
              <template #error>
                <div class="lab-cover-fallback detail-cover-fallback">暂无图片</div>
              </template>
            </el-image>
            <div class="detail-info">
              <div class="detail-row">
                <span class="detail-label">位置</span>{{ detail.location ?? '未填写' }}
              </div>
              <div class="detail-row">
                <span class="detail-label">容量</span>{{ detail.capacity }} 人
              </div>
              <div class="detail-row">
                <span class="detail-label">开放时间</span>{{ detail.open_time }} ~ {{ detail.close_time }}
              </div>
              <div class="detail-row">
                <span class="detail-label">简介</span>{{ detail.description ?? '暂无简介' }}
              </div>
            </div>
          </div>

          <!-- 挂载的设备列表：当前实验室下所有设备（含禁用的，供管理员参考） -->
          <div class="detail-devices-title">实验室设备（{{ detail.equipment.length }} 种）</div>
          <el-table v-if="detail.equipment.length > 0" :data="detail.equipment" size="small">
            <el-table-column prop="name" label="设备名称" min-width="120" />
            <el-table-column prop="spec" label="型号规格" min-width="110" />
            <el-table-column prop="quantity" label="数量" width="70" />
            <el-table-column prop="description" label="说明" min-width="140" show-overflow-tooltip />
            <!-- 每台设备都能直接预约：禁用设备按钮置灰不可点 -->
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  size="small"
                  :disabled="row.status !== 1"
                  @click="bookDevice(row)"
                >立即预约</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="该实验室暂无设备" :image-size="60" />
        </template>
      </div>
      <!-- 弹窗底部操作区：预约对象是当前查看的整个实验室 -->
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" :disabled="detailLoading" @click="openBooking(detail)">
          预约整个实验室
        </el-button>
      </template>
    </el-dialog>

    <!-- 预约弹窗：选择日期、时段、预约对象（整间实验室或指定设备） -->
    <el-dialog v-model="bookingVisible" title="预约实验室" width="480px" append-to-body>
      <!-- append-to-body：预约弹窗叠在设备列表弹窗之上，挂到 body 避免嵌套层级问题 -->
      <div v-loading="bookingLoading" class="booking-body">
        <el-form ref="bookingFormRef" :model="bookingForm" :rules="bookingRules" label-width="80px">
          <!-- 只读展示当前预约的实验室，disabled 输入框比纯文字更整齐 -->
          <el-form-item label="实验室">
            <el-input :model-value="bookingLab?.name" disabled />
          </el-form-item>
        <el-form-item label="预约对象">
          <el-radio-group v-model="bookingForm.target">
            <el-radio-button value="lab">整个实验室</el-radio-button>
            <el-radio-button value="device">指定设备</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <!-- 只有选「指定设备」才出现设备下拉 -->
        <el-form-item v-if="bookingForm.target === 'device'" label="选择设备" prop="equipment_id">
          <el-select
            v-model="bookingForm.equipment_id"
            placeholder="请选择设备"
            style="width: 100%"
          >
            <el-option
              v-for="eq in availableEquipments"
              :key="eq.id"
              :label="eq.spec ? `${eq.name}（${eq.spec}）` : eq.name"
              :value="eq.id"
            />
          </el-select>
          <div v-if="availableEquipments.length === 0" class="no-device-tip">
            该实验室暂无可用设备，可预约整个实验室
          </div>
        </el-form-item>
        <!-- value-format 与后端约定对齐：日期 YYYY-MM-DD -->
        <el-form-item label="日期" prop="date">
          <el-date-picker
            v-model="bookingForm.date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
            :disabled-date="disablePastDate"
          />
        </el-form-item>
        <!-- el-time-select：下拉选时间点，选项范围限定在实验室开放时间内，步长半小时 -->
        <el-form-item label="开始时间" prop="start_time">
          <el-time-select
            v-model="bookingForm.start_time"
            :start="bookingLab?.open_time"
            :end="bookingLab?.close_time"
            step="00:30"
            placeholder="选择开始时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-time-select
            v-model="bookingForm.end_time"
            :start="bookingLab?.open_time"
            :end="bookingLab?.close_time"
            step="00:30"
            placeholder="选择结束时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="bookingForm.remark"
            type="textarea"
            :rows="2"
            maxlength="200"
            show-word-limit
            placeholder="选填，如实验内容、人数等"
          />
        </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="bookingVisible = false">取消</el-button>
        <el-button type="primary" :loading="bookingSaving" @click="submitBooking">
          提交预约
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

/* 右上角操作区：状态过滤和搜索框水平排列 */
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 卡片网格：自动换行，每张卡片固定宽度，间距 16px */
.lab-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  min-height: 200px;
}

/* 空状态占位横跨整行 */
.grid-empty {
  grid-column: 1 / -1;
}

/* 实验室卡片：鼠标悬停浮起效果（点击交互在卡片底部按钮上） */
.lab-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.lab-card:hover {
  transform: translateY(-4px);
}

/* 封面图：固定高度裁切填满 */
.lab-cover {
  width: 100%;
  height: 140px;
  display: block;
  border-radius: 6px;
}

/* 无图时的灰色占位 */
.lab-cover-fallback {
  width: 100%;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  color: #a0aec0;
  font-size: 13px;
}

/* 详情弹窗里的封面占位稍矮一点 */
.detail-cover-fallback {
  height: 130px;
  border-radius: 6px;
}

/* 卡片文字区 */
.lab-body {
  padding-top: 10px;
}

.lab-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.lab-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
}

.lab-meta {
  font-size: 12px;
  color: #8492a6;
  line-height: 20px;
}

/* 简介最多显示两行，超出省略 */
.lab-desc {
  font-size: 12px;
  color: #8492a6;
  margin: 6px 0 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 分页控件靠右放置 */
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 详情弹窗：封面上部布局 */
.detail-body {
  min-height: 200px;
}

.detail-top {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.detail-cover {
  width: 200px;
  height: 130px;
  flex-shrink: 0; /* 禁止被右侧信息挤压 */
  border-radius: 6px;
}

.detail-info {
  flex: 1;
}

.detail-row {
  font-size: 13px;
  color: #4e5969;
  line-height: 26px;
}

.detail-label {
  display: inline-block;
  width: 64px;
  color: #8492a6;
}

/* 设备列表小标题 */
.detail-devices-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 10px;
}

/* 预约弹窗内容区：给 v-loading 一个最小高度，避免加载时弹窗塌陷 */
.booking-body {
  min-height: 200px;
}

/* 卡片底部操作区：两个按钮水平排列 */
.lab-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

/* 预约弹窗里「无可用设备」的提示文字 */
.no-device-tip {
  font-size: 12px;
  color: #e6a23c;
  line-height: 20px;
  margin-top: 4px;
}
</style>
