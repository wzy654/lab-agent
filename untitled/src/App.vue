<script setup lang="ts">
// 根组件只做路由出口：侧边栏布局在 layouts/MainLayout.vue，登录页全屏独立
</script>

<template>
  <!-- router-view：路由渲染出口，当前 URL 匹配的页面组件会显示在这里 -->
  <router-view />
</template>
