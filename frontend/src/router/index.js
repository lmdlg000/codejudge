import { createRouter, createWebHistory, createWebHashHistory } from 'vue-router'
import { applyTdk, TDK_HOME, TDK_HISTORY, TDK_ABOUT } from '../utils/tdk.js'

// GitHub Pages 等静态托管（无 history 回退）：构建时 VITE_ROUTER_MODE=hash
const historyMode = import.meta.env.VITE_ROUTER_MODE === 'hash'

const routes = [
  {
    path: '/',
    name: 'problems',
    component: () => import('../pages/ProblemList.vue'),
    meta: { tdk: TDK_HOME }
  },
  {
    path: '/problems/:pid',
    name: 'problem-detail',
    component: () => import('../pages/ProblemDetail.vue')
  },
  {
    path: '/submissions',
    name: 'submissions',
    component: () => import('../pages/SubmissionList.vue'),
    meta: { tdk: TDK_HISTORY }
  },
  {
    path: '/submissions/:sid',
    name: 'submission-detail',
    component: () => import('../pages/SubmissionDetail.vue')
  },
  {
    path: '/admin-review',
    name: 'admin-review',
    component: () => import('../pages/ReviewPage.vue')
  },
  {
    path: '/review',
    redirect: '/admin-review'
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('../pages/About.vue'),
    meta: { tdk: TDK_ABOUT }
  },
  {
    // Δ1-1：登录/注册合一（不设 /register）；TDK 与 noindex 在页内套用
    path: '/login',
    name: 'login',
    component: () => import('../pages/LoginPage.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../pages/NotFound.vue')
  }
]

const router = createRouter({
  history: historyMode ? createWebHashHistory() : createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, top: 72 }
    return { top: 0 }
  }
})

// 静态 TDK 在路由切换时套用（动态页在各自页面内套用）
router.afterEach((to) => {
  if (to.meta && to.meta.tdk) applyTdk(to.meta.tdk)
})

export default router
