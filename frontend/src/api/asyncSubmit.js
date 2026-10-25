/**
 * 异步评测提交（Judge0 确定性执行 + AI 语义评判 + 人工复核流）—— supabase 模式专用。
 * 提交：POST {SUPABASE_URL}/functions/v1/judge → 立即回执 {submissionId, status:'judging'}
 * 后台：Judge0(wait=true) 实跑样例 → AI 基于运行数据评分 → ai_scored | pending_review
 * 裁决：POST {SUPABASE_URL}/functions/v1/admin-review → human_reviewed_pass | human_reviewed_fail
 * 状态：Supabase Realtime（postgres_changes on submissions）推送，零轮询零刷新。
 */
import { supabase } from './supabase.js'
import { ApiError, ERROR_HINTS } from './errors.js'

function functionsBase() {
  const url = (import.meta.env.VITE_SUPABASE_URL || '').replace(/\/$/, '')
  return `${url}/functions/v1`
}

async function callFunction(name, payload, token) {
  let res
  try {
    res = await fetch(`${functionsBase()}/${name}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        Authorization: `Bearer ${token}`,
        apikey: import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || ''
      },
      body: JSON.stringify(payload)
    })
  } catch {
    throw new ApiError('NETWORK_ERROR', ERROR_HINTS.NETWORK_ERROR.hint, 0)
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
    const code = body && body.error && body.error.code ? body.error.code : 'INTERNAL_ERROR'
    const message =
      body && body.error && body.error.message
        ? body.error.message
        : (ERROR_HINTS[code] || ERROR_HINTS.INTERNAL_ERROR).hint
    throw new ApiError(code, message, res.status)
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
    .subscribe()
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
