/**
 * 认证组合式函数（site-spec 13.1 会话存取约定）。
 * 模块级单例状态：session / user；onAuthStateChange 挂事件（Δ2 风险①：
 * 登录成功 toast 与回跳跟 SIGNED_IN 事件，不跟调用时机）。
 */
import { ref, computed } from 'vue'
import { supabase, authMode, siteRootUrl } from '../api/supabase.js'
import { getHealth } from '../api/client.js'

const session = ref(null)
const user = ref(null)
const ready = ref(false)

/**
 * 两端不一致降级（13.4）：env 已配但后端 health.supabase_configured=false
 * → 降级为 local 行为，并在关于页提示配置不一致。
 */
const modeDegraded = ref(false)

let inited = false
let hadSession = false
let listeners = []
let toastFn = null

/** 生效 authMode：env 配置 且 未因两端不一致降级 */
export const effectiveAuthMode = computed(() => authMode && !modeDegraded.value)

/** 配置不一致（供关于页提示） */
export const configMismatch = computed(() => authMode && modeDegraded.value)

/** 是否已登录 */
export const isLoggedIn = computed(() => !!session.value && !!user.value)

/** 展示名：GitHub 用户名 > username > 邮箱 */
export const displayName = computed(() => {
  const u = user.value
  if (!u) return ''
  const meta = u.user_metadata || {}
  return meta.user_name || meta.preferred_username || meta.username || u.email || ''
})

/** 邮箱（下拉灰字行） */
export const emailText = computed(() => (user.value && user.value.email) || '')

/** 当前 access_token（提交带 Authorization 头用） */
export function accessToken() {
  return session.value ? session.value.access_token : null
}

/** 事件订阅：SIGNED_IN / SIGNED_OUT（返回退订函数） */
export function onAuthEvent(fn) {
  listeners.push(fn)
  return () => {
    listeners = listeners.filter((f) => f !== fn)
  }
}

function emitAuth(event, s, reason) {
  listeners.forEach((fn) => {
    try {
      fn(event, s, reason)
    } catch {
      /* 监听器异常不阻断 */
    }
  })
}

/** 登录成功回跳目标（被拦截的题目页等） */
const LOGIN_REDIRECT_KEY = 'codejudge-login-redirect'

/** 会话过期事件名（API 层 401 → 全局广播 → 统一登出清理，杜绝坏会话换票风暴） */
export const AUTH_EXPIRED_EVENT = 'codejudge-auth-expired'

/**
 * 坏会话清理：本地存的会话若已失效（过期/换票失败/撤销），
 * autoRefreshToken 会以 ~30s 周期无限换票产生 401 风暴——
 * 立即本地登出清存储，一次性止血。
 */
async function clearBrokenSession(reason) {
  hadSession = false
  session.value = null
  user.value = null
  try {
    await supabase.auth.signOut({ scope: 'local' })
  } catch {
    /* 本地清理优先，服务端撤销失败不阻断 */
  }
  if (toastFn && reason !== 'unreachable') {
    toastFn('登录状态已过期，请重新登录。')
  }
  emitAuth('SESSION_EXPIRED', null, reason)
}

/** 会话自检：恢复的会话经 getUser 验证，失效即清（网络异常不误登出） */
async function validateSession() {
  if (!session.value) return
  try {
    const { data, error } = await supabase.auth.getUser()
    if (error) {
      const st = error.status || 0
      if (st === 401 || st === 403 || /jwt|token|invalid/i.test(error.message || '')) {
        await clearBrokenSession('invalid')
      }
      return
    }
    if (!data || !data.user) await clearBrokenSession('invalid')
  } catch {
    /* 网络异常：保留会话，不误登出 */
  }
}

export function rememberRedirect(path) {
  try {
    if (path && path !== '/login') sessionStorage.setItem(LOGIN_REDIRECT_KEY, path)
  } catch {
    /* ignore */
  }
}

function consumeRedirect() {
  try {
    const v = sessionStorage.getItem(LOGIN_REDIRECT_KEY)
    sessionStorage.removeItem(LOGIN_REDIRECT_KEY)
    return v || '/'
  } catch {
    return '/'
  }
}

/**
 * App boot：恢复会话 + 挂 onAuthStateChange + health 一致性检查。
 * @param {{ router?: import('vue-router').Router, toast?: (msg:string)=>void }} deps
 */
export function initAuth(deps = {}) {
  if (inited || !authMode || !supabase) {
    ready.value = true
    return
  }
  inited = true
  toastFn = deps.toast || null

  // 启动恢复登录态 + 坏会话自检（防 autoRefresh 无限 401）
  supabase.auth.getSession().then(({ data }) => {
    session.value = data && data.session ? data.session : null
    user.value = session.value ? session.value.user : null
    hadSession = !!session.value
    ready.value = true
    validateSession()
  })

  supabase.auth.onAuthStateChange((event, s) => {
    session.value = s || null
    user.value = s ? s.user : null

    if (event === 'TOKEN_REFRESH_FAILED') {
      // 换票失败 ≠ 会话无效（网络抖动/限流也会触发）：先验证，确认失效才清
      validateSession()
      return
    }

    if (event === 'SIGNED_IN' && s) {
      // 首次 SIGNED_IN：upsert profiles（RLS 限本人，on conflict do nothing）
      const meta = s.user && s.user.user_metadata ? s.user.user_metadata : {}
      const username = meta.user_name || meta.preferred_username || meta.username || null
      supabase
        .from('profiles')
        .upsert(
          { id: s.user.id, username },
          { onConflict: 'id', ignoreDuplicates: true }
        )
        .then(() => {}, () => {})

      // 仅在「无会话 → 有会话」时弹 toast 并回跳（避免刷新/换票重复弹）
      if (!hadSession) {
        hadSession = true
        if (deps.toast) deps.toast('登录成功。可以提交判题了。')
        const target = consumeRedirect()
        if (deps.router) deps.router.replace(target)
      }
    } else if (event === 'SIGNED_OUT') {
      hadSession = false
    }
    emitAuth(event, s)
  })

  // 两端一致性：后端未配 Supabase 则降级为 local 行为
  getHealth()
    .then((h) => {
      if (h && h.supabase_configured === false) modeDegraded.value = true
    })
    .catch(() => {
      /* 后端不可达时不降级，保持 env 判定 */
    })

  // API 层 401 广播 → 验证后决定：确认会话失效才清理（防误登出）
  window.addEventListener(AUTH_EXPIRED_EVENT, () => {
    if (session.value) validateSession()
  })
}

/**
 * 邮箱密码注册（username 选填 → raw_user_meta_data；表单无用户名字段时取邮箱前缀）。
 * @param {{email:string, password:string, username?:string}} form
 */
export function signUp(form) {
  return supabase.auth.signUp({
    email: form.email,
    password: form.password,
    options: { data: { username: form.username || form.email.split('@')[0] } }
  })
}

/** 邮箱密码登录 */
export function signInWithPassword(form) {
  return supabase.auth.signInWithPassword({
    email: form.email,
    password: form.password
  })
}

/** GitHub OAuth（redirectTo = 站点根 URL，不带 #/） */
export function signInWithGitHub() {
  return supabase.auth.signInWithOAuth({
    provider: 'github',
    options: { redirectTo: siteRootUrl() }
  })
}

/** 退出登录 */
export function signOut() {
  return supabase.auth.signOut()
}

export { authMode }
