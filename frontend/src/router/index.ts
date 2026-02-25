import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/views/LayoutView.vue'),
      children: [
        { path: '', redirect: '/dashboard' },
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
          meta: { title: '工作台' },
        },
        // 市场需求管理
        {
          path: 'market/leads',
          name: 'Leads',
          component: () => import('@/views/market/LeadList.vue'),
          meta: { title: '线索管理' },
        },
        {
          path: 'market/opportunities',
          name: 'Opportunities',
          component: () => import('@/views/market/OpportunityList.vue'),
          meta: { title: '商机管理' },
        },
        {
          path: 'market/quotations',
          name: 'Quotations',
          component: () => import('@/views/market/QuotationList.vue'),
          meta: { title: '报价管理' },
        },
        // 客户管理
        {
          path: 'customers',
          name: 'Customers',
          component: () => import('@/views/customer/CustomerList.vue'),
          meta: { title: '客户管理' },
        },
        {
          path: 'customers/:id',
          name: 'CustomerDetail',
          component: () => import('@/views/customer/CustomerDetail.vue'),
          meta: { title: '客户详情' },
        },
        // 合同/付款管理
        {
          path: 'contracts',
          name: 'Contracts',
          component: () => import('@/views/contract/ContractList.vue'),
          meta: { title: '合同管理' },
        },
        {
          path: 'contracts/:id',
          name: 'ContractDetail',
          component: () => import('@/views/contract/ContractDetail.vue'),
          meta: { title: '合同详情' },
        },
        {
          path: 'payments',
          name: 'Payments',
          component: () => import('@/views/contract/PaymentList.vue'),
          meta: { title: '收款管理' },
        },
        // 财务管理
        {
          path: 'finance/expenses',
          name: 'Expenses',
          component: () => import('@/views/finance/ExpenseList.vue'),
          meta: { title: '支出管理' },
        },
        // 任务管理
        {
          path: 'projects',
          name: 'Projects',
          component: () => import('@/views/task/ProjectList.vue'),
          meta: { title: '认证项目' },
        },
        {
          path: 'projects/:id',
          name: 'ProjectDetail',
          component: () => import('@/views/task/ProjectDetail.vue'),
          meta: { title: '项目详情' },
        },
        {
          path: 'tasks',
          name: 'Tasks',
          component: () => import('@/views/task/TaskList.vue'),
          meta: { title: '任务管理' },
        },
        // 系统管理
        {
          path: 'users',
          name: 'Users',
          component: () => import('@/views/system/UserList.vue'),
          meta: { title: '用户管理' },
        },
        {
          path: 'system/price-catalog',
          name: 'PriceCatalog',
          component: () => import('@/views/system/PriceCatalogView.vue'),
          meta: { title: '价格库' },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

// 全局路由守卫
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.token) return '/login'
  if (!auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      return '/login'
    }
  }
  // 普通用户禁止访问工作台
  if (to.path === '/dashboard' && auth.user?.role !== 'ROLE_ADMIN') {
    return '/projects'
  }
  return true
})

export default router
