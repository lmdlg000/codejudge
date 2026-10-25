<script setup>
/**
 * 应用壳：页头 + 路由视图 + 页脚 + Toast。
 * Δ1-3：local 模式全站提示条（可关闭，关闭态记 localStorage 不再出）。
 */
import { ref, onMounted } from 'vue'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import AlertBar from './components/AlertBar.vue'
import Toast from './components/Toast.vue'
import { authMode, initAuth } from './composables/useAuth.js'
import { useToast } from './composables/useToast.js'
import { useRouter } from 'vue-router'

const router = useRouter()
const toast = useToast()

/** local 模式提示条（Δ1-3）：可关闭，关闭态记 localStorage */
const BANNER_KEY = 'codejudge-local-banner-dismissed'
const showLocalBanner = ref(false)

function dismissBanner() {
  showLocalBanner.value = false
  try {
    localStorage.setItem(BANNER_KEY, '1')
  } catch {
    /* ignore */
  }
}

onMounted(() => {
  // SIGNED_IN 事件里统一弹 toast + 回跳（Δ2 风险①）
  initAuth({ router, toast: toast.show })
  if (!authMode) {
    try {
      showLocalBanner.value = localStorage.getItem(BANNER_KEY) !== '1'
    } catch {
      showLocalBanner.value = true
    }
  }
})
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <AlertBar
      v-if="showLocalBanner"
      tone="info"
      message="本地匿名模式：未配置云服务。判题照常，历史只存本机。"
      action-label="知道了"
      action-key="dismiss"
      class="app-banner"
      @action="dismissBanner"
    />
    <router-view />
    <AppFooter />
    <Toast />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-banner {
  border-radius: 0;
  border-left-width: 3px;
}
</style>
