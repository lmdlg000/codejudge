/**
 * API 客户端 —— 全站唯一 fetch 入口（site-spec 第 7 节约定）。
 * Base：同源 /api（开发经 Vite proxy 转发 127.0.0.1:8000；生产由 FastAPI 挂载）。
 * 任何组件不得裸写 fetch URL。
 */
import { ApiError, ERROR_HINTS, toApiError } from './errors.js'

// 同源默认；前端静态部署（如 GitHub Pages）时以 VITE_API_BASE 指向后端
// （import.meta.env 为 Vite 注入；Node 单测环境下安全降级为空）
const BASE = ((import.meta.env && import.meta.env.VITE_API_BASE) || '') + '/api'

/**
 * 统一请求：解析 JSON、把统一错误体转成 ApiError、网络失败兜底。
 * @param {string} path
 * @param {RequestInit} [options]
 */
async function request(path, options = {}) {
  let res
  try {
    res = await fetch(BASE + path, {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        ...(options.headers || {})
      },
      ...options
    })
  } catch {
    // 网络断开 / 后端未启动：无错误体
    throw new ApiError('NETWORK_ERROR', ERROR_HINTS.NETWORK_ERROR.hint, 0)
  }

  let body = null
  const text = await res.text()
  if (text) {
    try {
      body = JSON.parse(text)
    } catch {
      body = null
    }
  }

  if (!res.ok) {
    const code = body && body.error && body.error.code
      ? body.error.code
      : 'INTERNAL_ERROR'
    const message = body && body.error && body.error.message
      ? body.error.message
      : (ERROR_HINTS[code] || ERROR_HINTS.INTERNAL_ERROR).hint
    if (res.status === 401) {
      // 登录态失效（FastAPI 校验 JWT 失败）：广播清理坏会话，止住后续 401
      try {
        window.dispatchEvent(new Event('codejudge-auth-expired'))
      } catch {
        /* ignore */
      }
    }
    throw new ApiError(code, message, res.status)
  }

  return body
}

/** GET /api/health */
export function getHealth() {
  return request('/health')
}

/** GET /api/problems → { items: ProblemSummary[], total: number } */
export function getProblems() {
  return request('/problems')
}

/** GET /api/problems/{pid} → ProblemDetail */
export function getProblem(pid) {
  return request(`/problems/${encodeURIComponent(pid)}`)
}

/**
 * POST /api/submissions → SubmissionResult（同步判题，当场出全量结果）
 * supabase 模式带 Authorization: Bearer <access_token>（13.5；其余 GET 不强制）。
 * @param {{problem_id:string, source_code?:string, filename?:string, files?:{name:string,content:string}[], mode?:'acm'|'oi'}} payload
 * @param {string|null} [token] supabase access_token（local 模式不传）
 */
export function createSubmission(payload, token) {
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  return request('/submissions', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers
  })
}

/**
 * GET /api/submissions?problem_id&limit&offset → { items: SubmissionSummary[], total: number }
 * @param {{problem_id?:string, limit?:number, offset?:number}} [query]
 */
export function getSubmissions(query = {}) {
  const params = new URLSearchParams()
  if (query.problem_id) params.set('problem_id', query.problem_id)
  if (query.limit != null) params.set('limit', String(query.limit))
  if (query.offset != null) params.set('offset', String(query.offset))
  const qs = params.toString()
  return request('/submissions' + (qs ? `?${qs}` : ''))
}

/** GET /api/submissions/{sid} → SubmissionResult */
export function getSubmission(sid) {
  return request(`/submissions/${encodeURIComponent(sid)}`)
}

/** GET /api/examples?problem_id={pid} → { items: ExampleItem[] } */
export function getExamples(pid) {
  return request(`/examples?problem_id=${encodeURIComponent(pid)}`)
}

export { ApiError, toApiError }
