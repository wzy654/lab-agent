<script setup lang="ts">
import { computed, onMounted, reactive, ref, useTemplateRef } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Calendar, Clock, Lock, User } from '@element-plus/icons-vue'
import { homeApi } from '@/api/home'
import { authApi } from '@/api/auth'
import { fileApi } from '@/api/files'
import { fileUrl } from '@/utils/request'
import type { Booking, HomeStats, UploadResult } from '@/api/types'
// 全局共享的用户信息（登录时存入 localStorage，见 utils/user.ts）
// clearUser：退出登录用，清缓存的同时重置内存里的全局 userInfo
import { useUser } from '@/utils/user'

const stats = ref<HomeStats>()
const recent = ref<Booking[]>([])
const loading = ref(true)

// 用户信息：头像和悬停文案用；updateUser 用于保存后同步全局
const { userInfo, updateUser, clearUser } = useUser()
// 计算属性：头像显示姓名首字；拿不到用户信息时显示 ?
const initial = computed(() => userInfo.value?.name?.charAt(0) ?? '?')
// 计算属性：有头像时拼出完整图片地址；没有则返回 null（模板里回退到文字头像）
const avatarSrc = computed(() => (userInfo.value?.avatar ? fileUrl(userInfo.value.avatar) : null))
// 计算属性：角色中文文案（后端 role 是 'admin' / 'student'）
const roleText = computed(() =>
  userInfo.value?.role === 'admin' ? '管理员' : userInfo.value ? '学生' : '未登录',
)

// ---------- 个人信息弹窗 ----------
const profileVisible = ref(false)      // 弹窗显隐
const profileLoading = ref(false)      // 回显查询的 loading
const profileSaving = ref(false)       // 保存按钮的 loading，防止重复提交

// 表单数据：reactive 适合对象；账号/角色只读不进表单可编辑区
const profileForm = reactive({
  name: '',
  email: '',
  phone: '',
})

const avatarUploading = ref(false) // 头像上传中标记

// 表单实例：用于触发整表校验（validate 方法）
const profileFormRef = useTemplateRef('profileFormRef')

// 校验规则：姓名必填；邮箱/手机号选填但格式要合法
// validator 自定义校验：通过调 callback()，失败调 callback(new Error('原因'))
const profileRules = {
  name: [{ required: true, message: '姓名不能为空', trigger: 'blur' }],
  email: [
    {
      // 选填字段：空值放行，填了才校验格式
      validator: (_rule: unknown, value: string, callback: (err?: Error) => void) => {
        if (value && !/^[\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,}$/.test(value)) {
          callback(new Error('邮箱格式不正确'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  phone: [
    {
      validator: (_rule: unknown, value: string, callback: (err?: Error) => void) => {
        if (value && !/^1[3-9]\d{9}$/.test(value)) {
          callback(new Error('手机号格式不正确'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 换头像：el-upload 选中图片后立刻走这里（:http-request 接管了默认上传行为）
// option.file 是用户选中的 File 对象
async function handleAvatarUpload(option: { file: File }) {
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
  avatarUploading.value = true
  try {
    // 第一步：把图片传给文件接口，拿到相对路径（如 uploads/xxx.png）
    const result: UploadResult = await fileApi.uploadFile(file)
    // 第二步：把路径写进当前用户的 avatar 字段
    const updated = await authApi.updateProfile({ avatar: result.url })
    // 第三步：刷新全局用户信息，右上角头像立即变成新图片
    updateUser(updated)
    ElMessage.success('头像已更新')
  } catch (e) {
    // 失败必须提示（如「文件类型不允许」「文件过大」），不能静默吞掉
    ElMessage.error(e instanceof Error ? e.message : '头像上传失败')
  } finally {
    avatarUploading.value = false
  }
}

// 点击「个人信息」：打开弹窗并调接口查最新信息回显（避免显示 localStorage 里的旧数据）
async function openProfile() {
  profileVisible.value = true
  profileLoading.value = true
  try {
    const info = await authApi.me()   // GET /user/info，自动带 token
    updateUser(info)                  // 顺便同步全局用户信息
    profileForm.name = info.name ?? ''
    profileForm.email = info.email ?? ''
    profileForm.phone = info.phone ?? ''
  } catch {
    // 请求失败时用本地缓存兜底回显
    profileForm.name = userInfo.value?.name ?? ''
  } finally {
    profileLoading.value = false
  }
}

// ---------- 修改密码弹窗 ----------
const router = useRouter()
const pwdVisible = ref(false)          // 改密码弹窗显隐
const pwdSaving = ref(false)           // 提交 loading

// 密码表单：三个输入框都用 el-input 的 show-password，默认打码可切换明文
const pwdForm = reactive({
  old: '',
  new: '',
  confirm: '',
})

// 弹窗里表单实例（和 profileFormRef 同理，用于触发校验）
const pwdFormRef = useTemplateRef('pwdFormRef')

const pwdRules = {
  old: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 30, message: '密码长度为 6-30 位', trigger: 'blur' },
    {
      // 新密码不能和旧密码相同（后端也校验了，前端提前拦截体验更好）
      validator: (_rule: unknown, value: string, callback: (err?: Error) => void) => {
        if (value && value === pwdForm.old) {
          callback(new Error('新密码不能与旧密码相同'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      // 两次输入必须一致
      validator: (_rule: unknown, value: string, callback: (err?: Error) => void) => {
        if (value && value !== pwdForm.new) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 打开修改密码弹窗，并清空上一次的输入
function openPwd() {
  pwdForm.old = ''
  pwdForm.new = ''
  pwdForm.confirm = ''
  pwdVisible.value = true
}

// 提交改密码：成功后自动登出，强制用新密码重新登录
async function savePassword() {
  // 校验不通过时 validate() 会 reject，catch 住直接返回（红字已显示在输入框下）
  try {
    await pwdFormRef.value?.validate()
  } catch {
    return
  }
  pwdSaving.value = true
  try {
    await authApi.updatePassword(pwdForm.old, pwdForm.new)
    ElMessage.success('密码修改成功，请重新登录')
    pwdVisible.value = false
    profileVisible.value = false
    clearUser()            // 清缓存 + 重置内存里的全局用户信息（见 utils/user.ts）
    router.push('/login')  // 回到登录页
  } catch (e) {
    // 失败必须提示（如「旧密码错误」），不能静默吞掉
    ElMessage.error(e instanceof Error ? e.message : '密码修改失败')
  } finally {
    pwdSaving.value = false
  }
}

// 保存修改：校验通过后调 PUT /user/update
// 关键规则：只提交「非空」的字段——空白项不上送，避免把数据库里已有的值置空
async function saveProfile() {
  // 校验不通过时 validate() 会 reject，catch 住直接返回（红字已显示在输入框下）
  try {
    await profileFormRef.value?.validate()
  } catch {
    return
  }
  // .trim() 去掉首尾空格，防止输入纯空格绕过「非空」判断
  const payload: { name?: string; email?: string; phone?: string } = {}
  if (profileForm.name.trim()) payload.name = profileForm.name.trim()
  if (profileForm.email.trim()) payload.email = profileForm.email.trim()
  if (profileForm.phone.trim()) payload.phone = profileForm.phone.trim()
  // 三个字段全为空：说明用户什么都没改（回显时字段可能为空），直接提示并中止
  if (Object.keys(payload).length === 0) {
    ElMessage.warning('请至少填写一项要保存的内容')
    return
  }
  profileSaving.value = true
  try {
    const updated = await authApi.updateProfile(payload)
    updateUser(updated)               // 用后端返回的最新数据刷新全局（头像首字等立即变）
    ElMessage.success('保存成功')
    profileVisible.value = false
  } catch (e) {
    // 失败必须提示，不能静默吞掉
    ElMessage.error(e instanceof Error ? e.message : '保存失败')
  } finally {
    profileSaving.value = false
  }
}

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
              <!-- el-avatar：有头像图片显示图片（src），否则显示姓名首字（默认插槽） -->
              <el-avatar class="avatar" :size="40" :src="avatarSrc">{{ initial }}</el-avatar>
            </template>
            <!-- 弹层内容：姓名 + 身份 + 个人信息入口 -->
            <div class="popover-name">{{ userInfo?.name ?? '未知用户' }}</div>
            <div class="popover-role">{{ roleText }}</div>
            <div class="popover-divider"></div>
            <!-- 点击打开个人信息弹窗 -->
            <div class="popover-action" @click="openProfile">
              <el-icon><User /></el-icon>
              <span>个人信息</span>
            </div>
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
      </section>
    </main>

    <!-- 个人信息弹窗：回显并可编辑，账号/角色只读，密码不涉及 -->
    <el-dialog v-model="profileVisible" title="个人信息" width="440px">
      <div v-loading="profileLoading" class="profile-body">
        <!-- 头像区：点击头像选图上传，el-upload 的 http-request 接管上传逻辑 -->
        <div class="profile-avatar">
          <el-upload :show-file-list="false" accept="image/*" :http-request="handleAvatarUpload">
            <el-badge :value="avatarUploading ? '上传中' : ''" type="info">
              <el-avatar class="profile-avatar-img" :size="64" :src="avatarSrc">{{ initial }}</el-avatar>
            </el-badge>
          </el-upload>
          <span class="profile-avatar-tip">点击头像更换</span>
        </div>

        <!-- el-form 绑定数据和规则；prop 必须和 rules 里的 key 对应，校验才会生效 -->
        <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-width="80px">
          <!-- disabled：只读项，账号和角色不允许修改 -->
          <el-form-item label="账号">
            <el-input :model-value="userInfo?.user_name" disabled />
          </el-form-item>
          <el-form-item label="角色">
            <el-input :model-value="roleText" disabled />
          </el-form-item>
          <el-form-item label="姓名" prop="name">
            <el-input v-model="profileForm.name" placeholder="请输入姓名" maxlength="30" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="profileForm.email" placeholder="请输入邮箱" maxlength="50" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="profileForm.phone" placeholder="请输入手机号" maxlength="20" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="profileVisible = false">取消</el-button>
        <!-- 修改密码：打开二级弹窗（不放在表单里是因为密码不属于「个人信息」） -->
        <el-button type="warning" plain :icon="Lock" @click="openPwd">修改密码</el-button>
        <el-button type="primary" :loading="profileSaving" @click="saveProfile">保存修改</el-button>
      </template>
    </el-dialog>

    <!-- 修改密码弹窗：成功后自动登出回登录页 -->
    <el-dialog v-model="pwdVisible" title="修改密码" width="400px" append-to-body>
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <!-- show-password：输入框右侧出现小眼睛，可切换明文/密文 -->
        <el-form-item label="旧密码" prop="old">
          <el-input v-model="pwdForm.old" type="password" show-password placeholder="请输入旧密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new">
          <el-input v-model="pwdForm.new" type="password" show-password placeholder="6-30 位" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm">
          <el-input
            v-model="pwdForm.confirm"
            type="password"
            show-password
            placeholder="请再次输入新密码"
            @keyup.enter="savePassword"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdSaving" @click="savePassword">确认修改</el-button>
      </template>
    </el-dialog>
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

/* 弹层内的分割线 */
.popover-divider {
  height: 1px;
  background: #ebeef5;
  margin: 8px 0;
}

/* 「个人信息」入口：横向排列图标+文字，hover 变主题色 */
.popover-action {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 0;
  border-radius: 6px;
  font-size: 13px;
  color: #1f2d3d;
  cursor: pointer;
  transition: all 0.2s;
}

.popover-action:hover {
  color: #1f6feb;
  background: #e8f1fd;
}

/* 弹窗表单区域：给 loading 遮罩一个最小高度，避免闪动 */
.profile-body {
  min-height: 180px;
}

/* 弹窗头像区：居中展示，头像 + 提示文字纵向排列 */
.profile-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
}

/* 弹窗里的大头像：去掉右边距让文字头像真正居中 */
.profile-avatar-img {
  background-color: #1f6feb;
  color: #fff;
  font-weight: 600;
  --el-avatar-bg-color: #1f6feb;
}

/* 「点击头像更换」提示 */
.profile-avatar-tip {
  font-size: 12px;
  color: #909399;
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
</style>
