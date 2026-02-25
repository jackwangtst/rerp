<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const menuItems = [
  { title: '工作台', path: '/dashboard', icon: 'Odometer', adminOnly: true },
  {
    title: '市场需求',
    icon: 'TrendCharts',
    children: [
      { title: '线索管理', path: '/market/leads' },
      { title: '商机管理', path: '/market/opportunities' },
      { title: '报价管理', path: '/market/quotations' },
    ],
  },
  { title: '客户管理', path: '/customers', icon: 'OfficeBuilding' },
  {
    title: '合同/付款',
    icon: 'Document',
    children: [
      { title: '合同管理', path: '/contracts' },
      { title: '收款管理', path: '/payments' },
    ],
  },
  {
    title: '财务管理',
    icon: 'Money',
    children: [
      { title: '支出管理', path: '/finance/expenses' },
    ],
  },
  {
    title: '任务管理',
    icon: 'Calendar',
    children: [
      { title: '认证项目', path: '/projects' },
      { title: '审核任务', path: '/tasks' },
    ],
  },
  {
    title: '系统管理',
    icon: 'Setting',
    adminOnly: true,
    children: [
      { title: '用户管理', path: '/users' },
      { title: '价格库', path: '/system/price-catalog' },
    ],
  },
]

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <el-container style="height: 100vh">
    <!-- 侧边栏 -->
    <el-aside width="220px" style="background:#001529">
      <div class="logo">任域通认证服务管理系统</div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#001529"
        text-color="#ffffffa0"
        active-text-color="#ffffff"
      >
        <template v-for="item in menuItems.filter(m => !m.adminOnly || auth.user?.role === 'ROLE_ADMIN')" :key="item.title">
          <el-sub-menu v-if="item.children" :index="item.title">
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item v-for="child in item.children" :key="child.path" :index="child.path">
              {{ child.title }}
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="item.path!">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶栏 -->
      <el-header style="background:#fff;border-bottom:1px solid #e8e8e8;display:flex;align-items:center;justify-content:flex-end;padding:0 24px">
        <el-dropdown @command="handleLogout">
          <span style="cursor:pointer;display:flex;align-items:center;gap:6px">
            <el-avatar :size="28" icon="UserFilled" />
            {{ auth.user?.full_name || auth.user?.username }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <!-- 主内容区 -->
      <el-main style="background:#f0f2f5;padding:20px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  font-weight: bold;
  letter-spacing: 2px;
  border-bottom: 1px solid #ffffff15;
}
</style>
