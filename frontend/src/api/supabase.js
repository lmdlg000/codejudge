/**
 * Supabase 客户端（site-spec 13.1 / 13.3 / 13.4）。
 * authMode = VITE_SUPABASE_URL 与 VITE_SUPABASE_PUBLISHABLE_KEY 均非空；
 * 未配置 = local 模式，**不初始化** supabase-js（全站行为保持匿名本地）。
 * 密钥边界：前端只允许 publishable 密钥（sb_publishable_ 前缀）；
 * secret 密钥只在 backend/.env，严禁出现在任何前端文件与构建产物。
 */
import { createClient } from '@supabase/supabase-js'

// import.meta.env 为 Vite 注入；Node 单测环境下安全降级为空 → local 模式
const ENV = import.meta.env || {}
const SUPABASE_URL = ENV.VITE_SUPABASE_URL || ''
const PUBLISHABLE_KEY = ENV.VITE_SUPABASE_PUBLISHABLE_KEY || ''

/** 前端 authMode 判定（env 双变量均非空） */
export const authMode = Boolean(SUPABASE_URL && PUBLISHABLE_KEY)

/** supabase-js 客户端；local 模式为 null */
export const supabase = authMode
  ? createClient(SUPABASE_URL, PUBLISHABLE_KEY, {
      auth: {
        autoRefreshToken: true,
        detectSessionInUrl: true,
        persistSession: true
      }
    })
  : null

/**
 * 站点根 URL（OAuth redirectTo，契约 13.6 硬约定：**不带 #/**）。
 * hash 模式下 pathname 即部署根；history 模式取 origin + BASE_URL。
 */
export function siteRootUrl() {
  const base = ENV.BASE_URL || '/'
  if (/^https?:\/\//.test(base)) return base.endsWith('/') ? base : base + '/'
  const origin = window.location.origin
  if (ENV.VITE_ROUTER_MODE === 'hash') {
    // 保留部署子路径（如 /repo/），去掉文件名
    const p = window.location.pathname.replace(/[^/]*$/, '')
    return origin + p
  }
  return origin + (base.startsWith('.') ? '/' : base)
}
