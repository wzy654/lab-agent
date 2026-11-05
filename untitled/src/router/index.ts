// ============================================================
// 路由配置 + 路由守卫
// 路由（router）：决定「URL 地址 → 显示哪个页面组件」的对应关系
// 例如访问 /login 显示登录页，访问 / 显示首页
// ============================================================

// vue-router 是 Vue 官方的路由库
// createRouter：创建路由实例；createWebHistory：使用 HTML5 history 模式
// （URL 里没有 # 号，如 /login 而不是 /#/login）
import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/auth'
// 主布局（侧边栏 + 内容区）：登录后的页面都套在这个外壳里
import MainLayout from '@/layouts/MainLayout.vue'

// 首页用静态导入（首屏页面，提前加载更快）
const HomeView = () => import('@/views/HomeView.vue')

const router = createRouter({
  // import.meta.env.BASE_URL：Vite 注入的基础路径，默认是 '/'
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ===== 登录页：顶层路由，全屏独立显示，不套侧边栏 =====
    {
      path: '/login', // 浏览器地址栏里的路径
      name: 'login', // 路由名称，可以用名字跳转：router.push({ name: 'login' })
      // () => import(...) 是「路由懒加载」：访问这个页面时才下载对应代码，
      // 让首屏加载更快
      component: () => import('@/views/LoginView.vue'),
    },
    // ===== 主布局：登录后可见的页面都作为它的 children（子路由） =====
    {
      path: '/',
      component: MainLayout, // 外壳（侧边栏布局）
      children: [
        {
          path: '', // path 为空表示访问 '/' 本身，即默认子页面
          name: 'home',
          component: HomeView,
        },
        {
          path: 'lab-center', // 实验室浏览：学生和管理员都能访问的浏览页
          name: 'lab-center',
          component: () => import('@/views/LabCenterView.vue'),
        },
        {
          path: 'labs', // 实验室管理：管理员专用的增删改查页
          name: 'labs',
          component: () => import('@/views/LabManageView.vue'),
        },
        {
          path: 'devices',
          name: 'devices',
          component: () => import('@/views/DeviceManageView.vue'),
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/UserManageView.vue'),
        },
        {
          path: 'ai',
          name: 'ai',
          component: () => import('@/views/AiChatView.vue'),
        },
      ],
    },
  ],
})

// ============ 路由守卫（重点） ============
// beforeEach：每次路由跳转「之前」都会先执行这个函数，相当于路由的安检门
// 它接收目标路由 to，返回值决定放行还是拦截：
//   - 返回 undefined / 不返回 → 放行，继续跳转
//   - 返回一个路由地址 → 中断本次跳转，改跳到返回的地址
router.beforeEach((to) => {
  const token = getToken() // 从 localStorage 读取登录凭证
  // 场景1：没登录（无 token）却想去其他页面 → 强制改去登录页
  // to.name !== 'login'：如果本来就是要去登录页，就放行，否则会死循环
  if (to.name !== 'login' && !token) {
    return { name: 'login' }
  }
  // 场景2：已登录（有 token）却访问登录页 → 没必要再看登录页，直接送回首页
  if (to.name === 'login' && token) {
    return { name: 'home' }
  }
  // 其他情况（已登录访问正常页面）：放行
})

// 导出路由实例，main.ts 里会挂载到 Vue 应用上（app.use(router)）
export default router
