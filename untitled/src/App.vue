<script setup lang="ts">
import { ref } from 'vue'
import { ChatDotRound, Cpu, House, Monitor, User } from '@element-plus/icons-vue'

const isCollapse = ref(false)
</script>

<template>
  <el-container class="layout">
    <el-aside :width="isCollapse ? '64px' : '200px'">
      <div class="logo">
        <el-icon :size="20"><Monitor /></el-icon>
        <span v-if="!isCollapse">实验室预约系统</span>
      </div>
      <el-menu
        default-active="/"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="menu"
      >
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <template #title>系统首页</template>
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
    </el-aside>

    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}

.el-aside {
  background-color: #001529;
  transition: width 0.2s;
  overflow-x: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.menu {
  height: calc(100vh - 60px);
  border-right: none;
}

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

.el-aside :deep(.el-menu-item.is-active) {
  background-color: #1f6feb;
  color: #fff;
}

.main {
  background-color: #f4f6f8;
  padding: 0;
  overflow: auto;
}
</style>
