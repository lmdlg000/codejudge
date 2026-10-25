/**
 * 异步评测提交（Judge0 确定性执行 + AI 语义评判 + 人工复核流）—— supabase 模式专用。
 * 提交：POST {SUPABASE_URL}/functions/v1/judge → 立即回执 {submissionId, status:'judging'}
 * 后台：Judge0(wait=true) 实跑样例 → AI 基于运行数据评分 → ai_scored | pending_review
 * 裁决：POST {SUPABASE_URL}/functions/v1/admin-review → human_reviewed_pass | human_reviewed_fail
 * 状态：Supabase Realtime（postgres_changes on submissions）推送，零轮询零刷新。
 */
import { supabase, freshAccessToken } from './supabase.js'
import { ApiError, ERROR_HINTS } from './errors.js'

function functionsBase() {
  const url = (import.meta.env.VITE_SUPABASE_URL || '').replace(/\/$/, '')
  return `${url}/functions/v1`
}

function sendFunction(name, payload, token) {
  return fetch(`${functionsBase()}/${name}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      // 新一代凭证体系：Edge Function 只读 Authorization（用户 JWT）；勿带 apikey 头
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

/** 解析错误体：自有统一错误体 {error:{code,message}} 优先用 message；平台网关形 {code,message} 归并中文提示 */
function errorFromBody(body, status) {
  const wrapped = body && body.error
  const e = wrapped || body || {}
  let code = e.code || 'INTERNAL_ERROR'
  if (wrapped) {
    // 自有统一错误体：message 为权威中文提示
    return new ApiError(code, e.message || (ERROR_HINTS[code] || ERROR_HINTS.INTERNAL_ERROR).hint, status)
  }
  if (!ERROR_HINTS[code] && /UNAUTHORIZED/i.test(code)) code = 'UNAUTHORIZED'
  const hint = ERROR_HINTS[code] && ERROR_HINTS[code].hint
  return new ApiError(code, hint || e.message || ERROR_HINTS.INTERNAL_ERROR.hint, status)
}

async function callFunction(name, payload, token) {
  // 每次现取活令牌（getSession 自动换票）；旧的入参令牌仅作兜底
  const t = (await freshAccessToken()) || token
  if (!t) {
    try {
      window.dispatchEvent(new Event('codejudge-auth-expired'))
    } catch {
      /* ignore */
    }
    throw new ApiError('UNAUTHORIZED', ERROR_HINTS.UNAUTHORIZED.hint, 401)
  }
  let res
  try {
    res = await sendFunction(name, payload, t)
  } catch {
    throw new ApiError('NETWORK_ERROR', ERROR_HINTS.NETWORK_ERROR.hint, 0)
  }
  // 401：先强制换票重试一次（令牌过期是常态，不该直接判死会话）
  if (res.status === 401 && supabase) {
    try {
      const { data } = await supabase.auth.refreshSession()
      const nt = data && data.session && data.session.access_token
      if (nt) res = await sendFunction(name, payload, nt)
    } catch {
      /* 换票失败：走下面的 401 处理 */
    }
  }
  const text = await res.text()
  let body = null
  if (text) {
    try {
      body = JSON.parse(text)
    } catch {
      body = null
    }
  }
  if (!res.ok) {
    if (res.status === 401) {
      // 重试后仍 401：广播会话复核（确认失效才登出，见 useAuth.validateSession）
      try {
        window.dispatchEvent(new Event('codejudge-auth-expired'))
      } catch {
        /* ignore */
      }
    }
    throw errorFromBody(body, res.status)
  }
  return body
}

/**
 * 提交评测（异步）。payload：{ problem_id, files|source_code, filename?, mode?, language?,
 *   problem: { title, statement_md, contest_type, limits, build_mode, samples } }
 * judge 函数会前置强制校验显式样例（任一失败 400 不落库）。
 * @returns {Promise<{submissionId:string, status:string}>}
 */
export async function submitForReview(payload, token) {
  const body = await callFunction('judge', payload, token)
  return {
    submissionId: body.submission_id || body.submissionId,
    status: body.status || 'judging'
  }
}

/**
 * 显式样例自测（dry_run，不落库）——双层校验的前端体验层。
 * @returns {Promise<{dry_run:boolean, passed:boolean, samples:Array<{name,passed,status,expected,actual,stderr}>}>}
 */
export async function verifySamples(payload, token) {
  return callFunction('judge', { ...payload, dry_run: true }, token)
}

/**
 * 配置自检（probe）：不执行任何代码，回报 Edge Secrets 配置状态。
 * 旧版函数不识别 probe 会返回 400「必须提供显式测试样例」→ 提示需重新部署。
 * @returns {Promise<{probe:boolean, uapi_configured:boolean, ai_configured:boolean, secret_configured:boolean}>}
 */
export async function probeConfig(token) {
  return callFunction('judge', { probe: true }, token)
}

/**
 * 人工复核裁决（admin-review）：{ submission_id, score, feedback, decision: 'pass'|'fail' }
 * @returns {Promise<{submission_id:string, status:string}>}
 */
export async function submitReview(payload, token) {
  return callFunction('admin-review', payload, token)
}

/**
 * 订阅某条提交的状态变更（Realtime；RLS 生效）。
 * @param {string} id submission id
 * @param {(row:any)=>void} onUpdate 收到 UPDATE 推送（payload.new）
 * @returns {() => void} 退订函数
 */
export function watchSubmission(id, onUpdate) {
  if (!supabase || !id) return () => {}
  const channel = supabase
    .channel(`sub-${id}`)
    .on(
      'postgres_changes',
      { event: 'UPDATE', schema: 'public', table: 'submissions', filter: `id=eq.${id}` },
      (payload) => onUpdate(payload.new)
    )
    .subscribe((status, err) => {
      // Realtime 失败静默降级（页面已有初值渲染，不产生未处理 Promise 异常）
      if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT' || err) {
        /* ignore */
      }
    })
  return () => {
    try {
      supabase.removeChannel(channel)
    } catch {
      /* ignore */
    }
  }
}

/**
 * 拉取单条云端提交（补订阅前的初值 / 刷新兜底）。
 * @param {string} id
 */
export async function fetchCloudSubmission(id) {
  if (!supabase) return null
  const { data, error } = await supabase
    .from('submissions')
    .select('*')
    .eq('id', id)
    .maybeSingle()
  if (error) return null
  return data
}

/** 生命周期状态（异步流）→ 中文短标签（human_reviewed_* 按变体区分） */
export const ASYNC_STATUS_LABEL = {
  judging: '评分中',
  ai_scored: 'AI 初评',
  pending_review: '待人工确认',
  human_reviewed: '复核完成',
  human_reviewed_pass: '复核通过',
  human_reviewed_fail: '复核未过'
}

/** human_reviewed 家族（human_reviewed / human_reviewed_pass / human_reviewed_fail） */
export function isHumanReviewed(status) {
  return typeof status === 'string' && status.startsWith('human_reviewed')
}

/** 该行是否处于异步评分流（而非旧同步判题结果） */
export function isAsyncRow(row) {
  if (!row) return false
  if (Array.isArray(row.cases) && row.cases.length > 0) return false
  const s = row.status
  return s === 'judging' || s === 'ai_scored' || s === 'pending_review' || isHumanReviewed(s)
}
