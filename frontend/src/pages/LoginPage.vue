<script setup>
/**
 * /login 登录 / 注册合一页（Δ2-1 终端风；文案逐字取 content-plan Δ1-1）。
 * 单页双态（登录 ↔ 注册 页内 tab），不设 /register。
 * 登录成功 toast 与回跳跟 SIGNED_IN 事件（useAuth.initAuth 内挂），本页只管表单。
 * noindex（Δ1-8）。
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthCard from '../components/AuthCard.vue'
import AppTabs from '../components/AppTabs.vue'
import TermInput from '../components/TermInput.vue'
import AppButton from '../components/AppButton.vue'
import AlertBar from '../components/AlertBar.vue'
import {
  authMode,
  effectiveAuthMode,
  isLoggedIn,
  signInWithPassword,
  signUp,
  signInWithGitHub,
  rememberRedirect
} from '../composables/useAuth.js'
import { ERROR_HINTS } from '../api/errors.js'
import { applyTdk, TDK_LOGIN } from '../utils/tdk.js'

const route = useRoute()
const router = useRouter()

const tab = ref('login') // login | signup
const email = ref('')
const password = ref('')
const confirm = ref('')

const fieldErrors = ref({ email: '', password: '', confirm: '' })
const authError = ref(null) // {code} → AlertBar
const submitting = ref(false)

const isLogin = computed(() => tab.value === 'login')

const tabs = [
  { key: 'login', label: '登录' },
  { key: 'signup', label: '注册' }
]

const cardTitle = computed(() => (isLogin.value ? 'auth · login' : 'auth · signup'))
const cardPrompt = computed(() => (isLogin.value ? '$ auth --login' : '$ auth --signup'))

/** 本地模式（未配置 Supabase）：表单禁用，只留说明 */
const cloudOff = computed(() => !effectiveAuthMode.value)

function switchTab(key) {
  tab.value = key
  // 切换即时清空：防误填混用（Δ2 取舍①，有意为之）
  password.value = ''
  confirm.value = ''
  fieldErrors.value = { email: '', password: '', confirm: '' }
  authError.value = null
}

/** 邮箱格式粗校验 */
function emailOk(v) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
}

function validate() {
  fieldErrors.value = { email: '', password: '', confirm: '' }
  let ok = true
  if (!emailOk(email.value.trim())) {
    fieldErrors.value.email = '邮箱格式不正确'
    ok = false
  }
  if (isLogin.value) {
    if (!password.value) {
      fieldErrors.value.password = '密码至少 8 位'
      ok = false
    }
  } else {
    if (password.value.length < 8) {
      fieldErrors.value.password = '密码至少 8 位'
      ok = false
    }
    if (confirm.value !== password.value) {
      fieldErrors.value.confirm = '两次输入的密码不一致'
      ok = false
    }
  }
  return ok
}

/** Supabase auth 错误 → content-plan Δ1-7 code */
function mapAuthError(e) {
  const raw = (e && (e.code || e.error_code || '')) || ''
  const msg = ((e && e.message) || '').toLowerCase()
  const known = [
    'invalid_credentials',
    'email_not_confirmed',
    'user_already_exists',
    'weak_password',
    'over_email_send_rate_limit',
    'provider_email_needs_verification',
    'over_request_rate_limit',
    'signup_disabled',
    'session_expired',
    'email_address_invalid'
  ]
  if (known.includes(raw)) return raw
  if (msg.includes('already registered') || msg.includes('already exists')) return 'user_already_exists'
  if (msg.includes('invalid login credentials') || msg.includes('invalid credentials')) return 'invalid_credentials'
  if (msg.includes('email not confirmed')) return 'email_not_confirmed'
  if (msg.includes('weak password') || msg.includes('password should')) return 'weak_password'
  if (msg.includes('rate limit')) return 'over_request_rate_limit'
  if (msg.includes('invalid email')) return 'email_address_invalid'
  return 'INTERNAL_ERROR'
}

async function onSubmit() {
  if (cloudOff.value || submitting.value) return
  authError.value = null
  if (!validate()) return
  submitting.value = true
  try {
    const form = {
      email: email.value.trim(),
      password: password.value
    }
    let result
    if (isLogin.value) {
      result = await signInWithPassword(form)
    } else {
      result = await signUp(form)
    }
    const err = result && result.error
    if (err) {
      const code = mapAuthError(err)
      authError.value = { code }
      // 同时落字段级提示（提交被拒时错误条 + 红字）
      if (code === 'user_already_exists') fieldErrors.value.email = '该邮箱已注册，请直接登录'
      if (code === 'invalid_credentials') fieldErrors.value.password = '邮箱或密码不正确'
      if (code === 'over_request_rate_limit') {
        fieldErrors.value.email = '尝试次数过多，请稍后再试'
      }
    }
    // 成功路径不在这里跳转：SIGNED_IN 事件里统一 toast + 回跳（Δ2 风险①）
  } catch (e) {
    const code = mapAuthError(e)
    authError.value = { code: ERROR_HINTS[code] ? code : 'INTERNAL_ERROR' }
  } finally {
    submitting.value = false
  }
}

function onGitHub() {
  if (cloudOff.value) return
  authError.value = null
  signInWithGitHub().catch((e) => {
    authError.value = { code: mapAuthError(e) }
  })
}

function onAuthAction(key) {
  if (key === 'goto-login') {
    // 「去登录」= 切到登录 tab
    switchTab('login')
  }
}

onMounted(() => {
  applyTdk(TDK_LOGIN)
  // 来源页（被拦截的题目页等）
  const redirect = route.query.redirect
  if (redirect) rememberRedirect(String(redirect))
  // 已登录访问登录页 → 回首页
  if (isLoggedIn.value) router.replace('/')
})

watch(isLoggedIn, (v) => {
  if (v) router.replace('/')
})
</script>

<template>
  <main class="page">
    <div class="page__main login">
      <h1>登录后提交判题，历史随账号走</h1>
      <p class="login__sub">
        邮箱注册登录，或用 GitHub 一键登录。未配置云服务时站点按本地匿名模式运行，此页不出现在导航里。
      </p>

      <!-- 本地模式：不出登录表单 -->
      <AlertBar
        v-if="cloudOff"
        tone="info"
        message="本地匿名模式：未配置云服务。判题照常，历史只存本机。"
        class="login__off"
      />

      <AuthCard v-else :title="cardTitle" :prompt="cardPrompt">
        <AppTabs v-model="tab" :tabs="tabs" aria-label="登录或注册" @update:model-value="switchTab" />

        <!-- 认证错误条：tab 下方、字段上方 -->
        <AlertBar
          v-if="authError"
          :code="authError.code"
          class="login__error"
          @action="onAuthAction"
        />

        <form class="login__form" novalidate @submit.prevent="onSubmit">
          <TermInput
            v-model="email"
            label="邮箱"
            type="email"
            placeholder="you@example.com"
            autocomplete="email"
            name="email"
            :error="fieldErrors.email"
          />
          <TermInput
            v-model="password"
            label="密码"
            type="password"
            :placeholder="isLogin ? '你的密码' : '至少 8 位'"
            :autocomplete="isLogin ? 'current-password' : 'new-password'"
            name="password"
            :error="fieldErrors.password"
          />
          <!-- 确认密码：仅注册态渲染（登录态 DOM 中不存在） -->
          <TermInput
            v-if="!isLogin"
            v-model="confirm"
            label="确认密码"
            type="password"
            placeholder="再输入一次"
            autocomplete="new-password"
            name="confirm"
            :error="fieldErrors.confirm"
          />

          <AppButton
            type="submit"
            variant="primary"
            block
            :loading="submitting"
          >{{ submitting ? (isLogin ? '登录中…' : '创建中…') : (isLogin ? '登录' : '创建账号') }}</AppButton>
        </form>

        <!-- 分隔线「或」 -->
        <div class="login__or" aria-hidden="true">
          <span class="login__or-line"></span>
          <span class="login__or-text">或</span>
          <span class="login__or-line"></span>
        </div>

        <!-- GitHub 按钮（oauth 变体，无括钮） -->
        <AppButton variant="oauth" block @click="onGitHub">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z" />
          </svg>
          <span>使用 GitHub 登录</span>
        </AppButton>

        <!-- 切换链接（只切 tab 不跳路由） -->
        <p class="login__switch">
          <button
            v-if="isLogin"
            type="button"
            class="login__switch-link"
            @click="switchTab('signup')"
          >没有账号，去注册</button>
          <button
            v-else
            type="button"
            class="login__switch-link"
            @click="switchTab('login')"
          >已有账号，去登录</button>
        </p>

        <p class="login__note">
          继续即表示：本地模式不收集任何数据；开启云同步后，判题历史存入你的账号并按账号隔离。
        </p>
      </AuthCard>
    </div>
  </main>
</template>

<style scoped>
.login {
  max-width: 640px;
  margin: 0 auto;
  padding-top: var(--space-10);
}

.login__sub {
  margin-top: var(--space-3);
  margin-bottom: var(--space-8);
  font-size: var(--text-caption);
  line-height: var(--lh-caption);
  color: var(--text-secondary);
  max-width: 640px;
}

.login__off {
  margin-bottom: var(--space-6);
}

.login__error {
  margin: var(--space-4) 0;
}

.login__form {
  margin-top: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.login__or {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin: var(--space-5) 0;
}

.login__or-line {
  flex: 1;
  height: 1px;
  background: var(--border);
}

.login__or-text {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
}

.login__switch {
  margin-top: var(--space-5);
  text-align: center;
}

.login__switch-link {
  background: none;
  border: none;
  padding: var(--space-2) var(--space-3);
  color: var(--primary);
  font-family: inherit;
  font-size: var(--text-body);
  cursor: pointer;
  border-radius: var(--radius-sm);
  /* 行高 ≥44px 热区 */
  min-height: 44px;
}

.login__switch-link:hover {
  color: var(--primary-hover);
  text-decoration: underline;
}

.login__note {
  margin-top: var(--space-5);
  font-size: 11px;
  line-height: 1.5;
  color: var(--text-muted);
  max-width: 36em;
}
</style>
