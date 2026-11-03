<script setup lang="ts">
// <script setup>：Vue 3 组合式 API 的语法糖，
// 里面定义的变量/函数在 <template> 模板中可以直接使用，无需 return

// ref：响应式数据。isCollapse 控制侧边栏是否折叠（true=折叠成窄条）
// $event 相关无需关心，el-aside 的 :width 绑定会根据它动态变宽变窄
import { ref } from 'vue'
// useRouter：获取路由实例，用于代码里跳转页面（router.push）
import { useRouter } from 'vue-router'
// 从 @element-plus/icons-vue 导入图标组件，模板里用 <el-icon> 包裹使用
import { ChatDotRound, Cpu, House, Monitor, SwitchButton, User } from '@element-plus/icons-vue'
// 登出方法：清 token 和用户信息（见 utils/auth.ts）
import { logout } from '@/utils/auth'

const router = useRouter()
const isCollapse = ref(false)

// 退出登录：清理本地缓存并回到登录页（后端暂无登出接口）
function handleLogout() {
  logout()
  router.push('/login') // 跳转到登录页
}
</script>

<template>
  <!-- el-container/el-aside/el-main：Element Plus 布局容器组件 -->
  <el-container class="layout">
    <!-- 侧边栏：宽度跟随 isCollapse 在 64px/200px 间切换 -->
    <el-aside :width="isCollapse ? '64px' : '200px'">
      <!-- 系统logo区域 -->
      <div class="logo">
        <el-icon :size="20"><Monitor /></el-icon>
        <span v-if="!isCollapse">实验室预约系统</span>
        <!-- v-if：条件渲染，折叠时隐藏文字只留图标 -->
      </div>
      <!-- el-menu：导航菜单；router 属性开启后，点击菜单项会跳转到 index 对应的路由 -->
      <el-menu
        default-active="/"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="menu"
      >
        <!-- index 就是路由地址，点击后自动跳转 -->
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <template #title>系统首页</template>
          <!-- #title 是具名插槽：折叠模式下悬浮显示的文字 -->
        </el-menu-item>
        <el-menu-item index="/labs">
          <el-icon><Monitor /></el-icon>
          <template #title>实验室管理</template>
        </el-menu-item>
        <el-menu-item index="/devices">
          <el-icon><Cpu /></el-icon>
          <template #title>设备管理</template>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        <el-menu-item index="/ai">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>AI 助手</template>
        </el-menu-item>
      </el-menu>

      <!-- 退出登录按钮：固定在侧边栏底部 -->
      <div class="logout" @click="handleLogout">
        <el-icon :size="16"><SwitchButton /></el-icon>
        <span v-if="!isCollapse">退出登录</span>
      </div>
    </el-aside>

    <!-- 内容区：登录后各页面的渲染出口（子路由页面显示在这里） -->
    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
/* scoped：样式只作用于当前组件，不会污染其他页面 */
.layout {
  height: 100vh; /* vh：视口高度单位，100vh = 占满整个屏幕高度 */
}

.el-aside {
  background-color: #001529; /* 深色背景 */
  transition: width 0.2s; /* 折叠/展开时的宽度过渡动画 */
  overflow-x: hidden; /* 横向内容超出时隐藏 */
  display: flex;
  flex-direction: column; /* flex 纵向排列：logo、菜单、退出按钮从上到下 */
}

.logo {
  height: 60px;
  display: flex;
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  gap: 8px; /* 子元素之间的间距 */
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0; /* 不允许被压缩 */
}

.menu {
  flex: 1; /* 占满剩余高度，把退出按钮挤到底部 */
  border-right: none;
}

.logout {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.65); /* 半透明白色文字 */
  cursor: pointer; /* 鼠标悬停显示手型 */
  flex-shrink: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.08); /* 与菜单之间的分割线 */
  transition: background-color 0.2s, color 0.2s;
}

.logout:hover {
  background-color: rgba(255, 255, 255, 0.08);
  color: #fff;
}

/* :deep()：让 scoped 样式能穿透作用于子组件（el-menu 内部元素） */
.el-aside :deep(.el-menu) {
  background-color: #001529;
}

.el-aside :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.65);
}

.el-aside :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.08);
  color: #fff;
}

/* .is-active：Element Plus 自动加在当前选中菜单项上的类名 */
.el-aside :deep(.el-menu-item.is-active) {
  background-color: #1f6feb;
  color: #fff;
}

.main {
  background-color: #f4f6f8;
  padding: 0;
  overflow: auto; /* 内容超出时出现滚动条 */
}
</style>
