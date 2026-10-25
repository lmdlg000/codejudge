<script setup>
/**
 * 页头导航（design-spec 5.6 + Δ2-2 用户菜单三态）。
 * ≥1024 横排链接 + 用户区；<1024 右侧抽屉（260px + 遮罩，Esc/遮罩关闭，焦点锁）。
 * 用户菜单三态：未登录「登录 / 注册」/ 已登录邮箱 mono 灰字 + ▾ 下拉 / 「本地模式」标签。
 * 退出二次确认：终端对话框壳（auth · signout），Esc=取消。
 */
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getHealth, FASTAPI_DISABLED } from '../api/client.js'
import {
  authMode,
  effectiveAuthMode,
  isLoggedIn,
  displayName,
  emailText,
  signOut
} from '../composables/useAuth.js'
import AuthCard from './AuthCard.vue'
import AppButton from './AppButton.vue'

const route = useRoute()
const router = useRouter()
const drawerOpen = ref(false)
const engineOk = ref(true)
/** 纯云模式（GitHub Pages 等：无 FastAPI，判题走 Edge Functions + UAPI） */
const cloudMode = FASTAPI_DISABLED && authMode
const drawerEl = ref(null)
const burgerEl = ref(null)

/* —— 用户菜单（桌面下拉）—— */
const menuOpen = ref(false)
const menuTrigger = ref(null)
const menuPanel = ref(null)

/* —— 退出二次确认 —— */
const signoutOpen = ref(false)
const signoutBusy = ref(false)
const signoutDialog = ref(null)

const links = [
  { to: '/', label: '题目', match: 'problems' },
  { to: '/submissions', label: '提交历史', match: 'submissions' },
  { to: '/about', label: '关于', match: 'about' }
]

const isLocalMode = computed(() => !authMode || !effectiveAuthMode.value)

/** 展示名（长名省略 + title，Δ2 风险③） */
const shownName = computed(() => displayName.value || emailText.value || '已登录')

function isActive(name) {
  return route.name === name
}

async function openDrawer() {
  drawerOpen.value = true
  await nextTick()
  const first = drawerEl.value && drawerEl.value.querySelector('a, button')
  if (first) first.focus()
}

function closeDrawer() {
  drawerOpen.value = false
  if (burgerEl.value) burgerEl.value.focus()
}

async function openMenu() {
  menuOpen.value = true
  await nextTick()
  const first = menuPanel.value && menuPanel.value.querySelector('button, a')
  if (first) first.focus()
}

function closeMenu(restoreFocus = true) {
  if (!menuOpen.value) return
  menuOpen.value = false
  if (restoreFocus && menuTrigger.value) menuTrigger.value.focus()
}

function toggleMenu() {
  if (menuOpen.value) closeMenu()
  else openMenu()
}

function askSignout() {
  closeMenu(false)
  if (drawerOpen.value) closeDrawer()
  signoutOpen.value = true
  nextTick(() => {
    const first = signoutDialog.value && signoutDialog.value.querySelector('button')
    if (first) first.focus()
  })
}

function cancelSignout() {
  signoutOpen.value = false
}

async function confirmSignout() {
  if (signoutBusy.value) return
  signoutBusy.value = true
  try {
    await signOut()
  } catch {
    /* 退出失败也清本地 UI 态 */
  } finally {
    signoutBusy.value = false
    signoutOpen.value = false
  }
}

function onDocClick(e) {
  // 点外关闭下拉
  if (!menuOpen.value) return
  const t = e.target
  if (
    menuPanel.value && menuPanel.value.contains(t) ||
    menuTrigger.value && menuTrigger.value.contains(t)
  ) return
  closeMenu(false)
}

function onKeydown(e) {
  if (e.key === 'Escape') {
    if (signoutOpen.value) {
      e.preventDefault()
      cancelSignout()
      return
    }
    if (menuOpen.value) {
      e.preventDefault()
      closeMenu()
      return
    }
    if (drawerOpen.value) {
      e.preventDefault()
      closeDrawer()
      return
    }
  }
  // 抽屉内焦点循环
  if (e.key === 'Tab' && drawerOpen.value && drawerEl.value) {
    const focusables = drawerEl.value.querySelectorAll('a, button:not([disabled])')
    if (!focusables.length) return
    const first = focusables[0]
    const last = focusables[focusables.length - 1]
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault()
      last.focus()
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault()
      first.focus()
    }
  }
  // 退出确认弹层焦点锁
  if (e.key === 'Tab' && signoutOpen.value && signoutDialog.value) {
    const focusables = signoutDialog.value.querySelectorAll('button:not([disabled])')
    if (!focusables.length) return
    const first = focusables[0]
    const last = focusables[focusables.length - 1]
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault()
      last.focus()
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault()
      first.focus()
    }
  }
}

watch(
  () => route.fullPath,
  () => {
    if (drawerOpen.value) drawerOpen.value = false
    closeMenu(false)
  }
)

onMounted(async () => {
  window.addEventListener('keydown', onKeydown)
  document.addEventListener('click', onDocClick)
  if (cloudMode) return // 云模式无本机引擎可探，避免无谓请求与误导黄灯
  try {
    const h = await getHealth()
    engineOk.value = h && h.status === 'ok'
  } catch {
    engineOk.value = false
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  document.removeEventListener('click', onDocClick)
})

function goLogin() {
  if (drawerOpen.value) closeDrawer()
  router.push('/login')
}
</script>

<template>
  <header class="header">
    <div class="header__inner container container--wide">
      <router-link to="/" class="header__logo" aria-label="CodeJudge 首页">
        <span class="header__prompt" aria-hidden="true">$</span>
        <!-- Logo 字标：CodeJudge + 终端光标方块（design-spec 9.1） -->
        <svg
          class="header__wordmark"
          viewBox="0 0 168 32"
          width="150"
          height="28"
          role="img"
          aria-label="CodeJudge"
        >
          <text
            x="0"
            y="23"
            font-family="var(--font-mono)"
            font-size="20"
            font-weight="700"
            fill="var(--text-primary)"
          >Code</text>
          <text
            x="58"
            y="23"
            font-family="var(--font-mono)"
            font-size="20"
            font-weight="700"
            fill="var(--primary)"
          >Judge</text>
          <rect x="140" y="8" width="8" height="18" rx="1" fill="var(--primary)" class="header__cursor" />
        </svg>
      </router-link>

      <!-- 桌面导航 -->
      <nav class="header__nav" aria-label="主导航">
        <router-link
          v-for="l in links"
          :key="l.match"
          :to="l.to"
          class="header__link"
          :class="{ 'header__link--active': isActive(l.match) }"
          :aria-current="isActive(l.match) ? 'page' : undefined"
        >{{ l.label }}</router-link>
      </nav>

      <div class="header__right">
        <div
          class="header__health"
          :title="cloudMode ? '云端评测（UAPI 执行 · AI 判分 · 人工复核）' : (engineOk ? '本机评测引擎就绪' : '引擎不可用')"
        >
          <span
            class="header__dot"
            :class="cloudMode || engineOk ? 'header__dot--ok' : 'header__dot--warn'"
            aria-hidden="true"
          ></span>
          <span class="micro header__health-text">{{ cloudMode ? '云端评测' : '本机评测' }}</span>
        </div>

        <!-- ===== 用户区三态（Δ2-2，桌面） ===== -->
        <div class="header__user">
          <!-- 本地模式：灰字标签，无交互 -->
          <span v-if="isLocalMode" class="header__local micro">本地模式</span>

          <!-- supabase + 未登录：文字链接（不用括钮） -->
          <router-link
            v-else-if="!isLoggedIn"
            to="/login"
            class="header__login-link"
          >登录 / 注册</router-link>

          <!-- 已登录：名 + ▾ 下拉 -->
          <template v-else>
            <button
              ref="menuTrigger"
              type="button"
              class="header__user-trigger"
              :aria-expanded="menuOpen ? 'true' : 'false'"
              aria-haspopup="menu"
              @click="toggleMenu"
            >
              <span class="header__username mono-data" :title="shownName">{{ shownName }}</span>
              <span class="header__caret" aria-hidden="true">▾</span>
            </button>
            <div
              v-show="menuOpen"
              ref="menuPanel"
              class="header__menu"
              role="menu"
            >
              <p class="header__menu-email mono-data" :title="emailText">{{ emailText }}</p>
              <button
                type="button"
                class="header__menu-item header__menu-item--danger"
                role="menuitem"
                @click="askSignout"
              >退出登录</button>
            </div>
          </template>
        </div>

        <!-- 移动端汉堡 -->
        <button
          ref="burgerEl"
          type="button"
          class="header__burger"
          aria-label="打开导航菜单"
          :aria-expanded="drawerOpen ? 'true' : 'false'"
          aria-controls="nav-drawer"
          @click="openDrawer"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true">
            <path d="M2 4h12M2 8h12M2 12h12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 抽屉遮罩 -->
    <div
      v-if="drawerOpen"
      class="header__overlay"
      aria-hidden="true"
      @click="closeDrawer"
    ></div>

    <!-- 右侧抽屉（<1024 用户区并入，Δ2-2） -->
    <nav
      v-show="drawerOpen"
      id="nav-drawer"
      ref="drawerEl"
      class="header__drawer"
      aria-label="移动端导航"
    >
      <div class="header__drawer-head">
        <span class="micro">导航</span>
        <button type="button" class="header__drawer-close" aria-label="关闭导航" @click="closeDrawer">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true">
            <path d="M4 4l8 8M12 4l-8 8" />
          </svg>
        </button>
      </div>

      <!-- 抽屉用户信息区 -->
      <div class="header__drawer-user">
        <span v-if="isLocalMode" class="header__local micro">本地模式</span>
        <template v-else-if="!isLoggedIn">
          <button type="button" class="header__login-link header__login-link--drawer" @click="goLogin">
            登录 / 注册
          </button>
        </template>
        <template v-else>
          <p class="header__drawer-email mono-data" :title="emailText">{{ emailText }}</p>
        </template>
      </div>

      <router-link
        v-for="l in links"
        :key="l.match"
        :to="l.to"
        class="header__drawer-link"
        :class="{ 'header__drawer-link--active': isActive(l.match) }"
        :aria-current="isActive(l.match) ? 'page' : undefined"
      >{{ l.label }}</router-link>

      <!-- 抽屉底部：退出登录（danger） -->
      <button
        v-if="isLoggedIn && !isLocalMode"
        type="button"
        class="header__drawer-signout"
        @click="askSignout"
      >退出登录</button>
    </nav>

    <!-- 退出二次确认（终端对话框壳，Δ2-2） -->
    <div
      v-if="signoutOpen"
      class="header__modal-overlay"
      aria-hidden="true"
      @click="cancelSignout"
    ></div>
    <div
      v-if="signoutOpen"
      ref="signoutDialog"
      class="header__modal"
      role="dialog"
      aria-modal="true"
      aria-label="退出登录确认"
    >
      <AuthCard title="auth · signout" prompt="$ auth --signout">
        <p class="header__modal-text">退出后本机浏览器清除登录状态，云端历史仍保留。</p>
        <div class="header__modal-actions">
          <AppButton variant="danger" :loading="signoutBusy" @click="confirmSignout">
            确认退出
          </AppButton>
          <AppButton variant="secondary" :disabled="signoutBusy" @click="cancelSignout">
            取消
          </AppButton>
        </div>
      </AuthCard>
    </div>
  </header>
</template>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: var(--z-header);
  height: var(--header-h);
  background: var(--bg-surface);
  border-bottom: var(--border);
}

.header__inner {
  height: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.header__logo {
  display: flex;
  align-items: center;
  flex: none;
}

.header__prompt {
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 700;
  color: var(--primary);
  margin-right: 6px;
}

.header__cursor {
  animation: cursor-blink 1.2s step-end infinite;
}

@keyframes cursor-blink {
  50% { opacity: 0; }
}

.header__nav {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  margin-left: var(--space-4);
}

.header__link {
  position: relative;
  display: inline-flex;
  align-items: center;
  height: var(--header-h);
  padding: 0 var(--space-1);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.header__link:hover {
  color: var(--primary-hover);
}

.header__link--active {
  color: var(--primary);
}

.header__link--active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 10px;
  height: 2px;
  background: var(--primary);
}

.header__right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.header__health {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.header__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex: none;
}

.header__dot--ok {
  background: var(--success-text);
}

.header__dot--warn {
  background: var(--warning-text);
}

.header__health-text {
  color: var(--text-muted);
}

/* —— 用户区三态 —— */
.header__user {
  position: relative;
  display: flex;
  align-items: center;
}

.header__local {
  color: var(--text-muted);
  white-space: nowrap;
}

.header__login-link {
  color: var(--primary);
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  padding: var(--space-2) var(--space-1);
  border-radius: var(--radius-sm);
  white-space: nowrap;
  background: none;
  border: none;
  font-family: inherit;
  cursor: pointer;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
}

.header__login-link:hover {
  text-decoration: underline;
  color: var(--primary-hover);
}

.header__login-link--drawer {
  padding-left: 0;
}

.header__user-trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  max-width: 200px;
  height: var(--control-h-sm);
  padding: 0 var(--space-2);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  /* 热区 44px */
  position: relative;
}

.header__user-trigger::after {
  content: '';
  position: absolute;
  inset: 50% auto auto 50%;
  width: 100%;
  height: 44px;
  min-width: 44px;
  transform: translate(-50%, -50%);
}

.header__user-trigger:hover {
  background: var(--bg-subtle);
}

.header__username {
  color: var(--text-secondary);
  font-size: 13px;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header__caret {
  color: var(--text-muted);
  font-size: 12px;
}

/* 下拉面板 240px（Δ2-2） */
.header__menu {
  position: absolute;
  top: calc(100% + var(--space-2));
  right: 0;
  width: 240px;
  background: var(--bg-surface);
  border: var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-1);
  z-index: calc(var(--z-header) + 1);
  overflow: hidden;
  animation: menu-in var(--dur-fast) var(--ease-out);
}

@keyframes menu-in {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.header__menu-email {
  margin: 0;
  padding: var(--space-3);
  font-size: 12px;
  color: var(--text-muted);
  border-bottom: var(--border);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header__menu-item {
  display: block;
  width: 100%;
  height: 40px;
  padding: 0 var(--space-3);
  border: none;
  background: transparent;
  text-align: left;
  font-family: inherit;
  font-size: var(--text-body);
  cursor: pointer;
  color: var(--text-primary);
}

.header__menu-item--danger:hover {
  background: var(--danger-bg);
  color: var(--danger-text);
}

.header__burger {
  display: none;
  width: 44px;
  height: 44px;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  cursor: pointer;
}

.header__burger:hover {
  background: var(--bg-subtle);
}

.header__overlay {
  position: fixed;
  inset: 0;
  background: var(--overlay);
  z-index: var(--z-drawer);
}

.header__drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 260px;
  height: 100vh;
  background: var(--bg-surface);
  border-left: var(--border);
  box-shadow: var(--shadow-1);
  z-index: calc(var(--z-drawer) + 1);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  transform: translateX(0);
  transition: transform var(--dur-base) var(--ease-out);
}

.header__drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
  color: var(--text-muted);
}

.header__drawer-user {
  padding: var(--space-2) var(--space-3);
  margin-bottom: var(--space-2);
  border-bottom: var(--border);
}

.header__drawer-email {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header__drawer-signout {
  margin-top: auto;
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 var(--space-3);
  border: none;
  border-radius: var(--radius);
  background: transparent;
  color: var(--danger-text);
  font-family: inherit;
  font-size: var(--text-body);
  font-weight: 500;
  cursor: pointer;
}

.header__drawer-signout:hover {
  background: var(--danger-bg);
}

.header__drawer-close {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
}

.header__drawer-close:hover {
  background: var(--bg-subtle);
  color: var(--text-primary);
}

.header__drawer-link {
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 var(--space-3);
  border-radius: var(--radius);
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.header__drawer-link--active {
  background: var(--primary-bg);
  color: var(--primary);
}

.header__drawer-link:hover {
  background: var(--bg-subtle);
}

/* —— 退出确认弹层 —— */
.header__modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--overlay);
  z-index: calc(var(--z-drawer) + 2);
}

.header__modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: calc(var(--z-drawer) + 3);
  width: min(440px, calc(100vw - 32px));
}

.header__modal-text {
  margin-bottom: var(--space-5);
  font-size: var(--text-body);
  line-height: var(--lh-body);
  color: var(--text-primary);
}

.header__modal-actions {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

@media (max-width: 1023px) {
  .header__nav {
    display: none;
  }

  .header__burger {
    display: inline-flex;
  }

  /* 桌面下拉用户区在窄屏隐藏（并入抽屉） */
  .header__user {
    display: none;
  }
}
</style>
