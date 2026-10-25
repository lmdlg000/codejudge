/**
 * 统一错误处理：site-spec 5.2 错误码表 + content-plan 5.1 前端提示（逐字）
 * + Δ1-7 认证与授权错误码 11 条（逐字）。
 * 契约：所有非 2xx 响应体为 {"error":{"code","message"}}。
 */

/** 8 个错误码 + 网络兜底（content-plan 5.1）+ Δ1 认证 11 条（content-plan Δ1-7） */
export const ERROR_HINTS = {
  VALIDATION_ERROR: {
    hint: '提交内容不合法，请检查后重试',
    extra: '文件名仅限字母、数字、_ . -，最长 64 字符',
    tone: 'error'
  },
  PROBLEM_NOT_FOUND: {
    hint: '题目不存在',
    extra: '回到题目列表选一道题',
    tone: 'error',
    action: 'goto-problems'
  },
  SUBMISSION_NOT_FOUND: {
    hint: '找不到该次提交',
    extra: '可能已被清理，回提交历史看看',
    tone: 'error',
    action: 'goto-submissions'
  },
  PAYLOAD_TOO_LARGE: {
    hint: '代码太长，请精简后重试',
    extra: '单文件上限 65536 字符，最多 20 个文件',
    tone: 'error'
  },
  JUDGE_TIMEOUT: {
    hint: '判题超时，请检查死循环后重试',
    extra: '整单判题上限 120 秒',
    tone: 'warning'
  },
  JUDGE_BUSY: {
    hint: '判题进行中，请稍候重试',
    extra: '同时只判一单，完成后可再提交',
    tone: 'warning'
  },
  ENGINE_UNAVAILABLE: {
    hint: '判题引擎不可用，请检查本机编译环境',
    extra: '确认 g++ 与 make 已安装并加入 PATH',
    tone: 'warning',
    action: 'goto-about'
  },
  INTERNAL_ERROR: {
    hint: '服务异常，请重试',
    extra: '反复出现请查看本机控制台日志',
    tone: 'error'
  },
  NETWORK_ERROR: {
    hint: '连不上判题服务，请确认本机后端已启动后刷新页面',
    extra: '',
    tone: 'error',
    action: 'reload'
  },

  /* —— Δ1 新增：统一错误体枚举（HTTP 401）—— */
  UNAUTHORIZED: {
    hint: '请先登录（登录状态可能已过期）',
    extra: '',
    tone: 'warning',
    action: 'goto-login'
  },

  /* —— Δ1-7：Supabase 认证错误码（auth 侧 code，逐字）—— */
  invalid_credentials: {
    hint: '邮箱或密码不正确',
    extra: '请检查大小写后重试',
    tone: 'error'
  },
  email_not_confirmed: {
    hint: '邮箱还没验证，请先打开验证邮件里的链接',
    extra: '没收到邮件请检查垃圾箱',
    tone: 'warning'
  },
  user_already_exists: {
    hint: '该邮箱已注册，请直接登录',
    extra: '',
    tone: 'warning',
    action: 'goto-login'
  },
  weak_password: {
    hint: '密码至少 8 位，请加长后重试',
    extra: '',
    tone: 'error'
  },
  over_email_send_rate_limit: {
    hint: '邮件发送过于频繁，请稍后再试',
    extra: '10 分钟后再试一次',
    tone: 'warning'
  },
  provider_email_needs_verification: {
    hint: 'GitHub 账号邮箱未验证',
    extra: '请到 GitHub 设置里验证邮箱后重试',
    tone: 'warning'
  },
  over_request_rate_limit: {
    hint: '请求过于频繁，请稍后再试',
    extra: '',
    tone: 'warning'
  },
  signup_disabled: {
    hint: '注册当前未开放，请联系管理员',
    extra: '',
    tone: 'error'
  },
  session_expired: {
    hint: '登录状态已过期，请重新登录',
    extra: '',
    tone: 'warning',
    action: 'goto-login'
  },
  email_address_invalid: {
    hint: '邮箱格式不正确',
    extra: '请检查后重试',
    tone: 'error'
  }
}

/** 契约约定的统一错误体 */
export class ApiError extends Error {
  /**
   * @param {string} code 错误码枚举
   * @param {string} message 服务端中文信息（可直接展示）
   * @param {number} [httpStatus]
   */
  constructor(code, message, httpStatus) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.httpStatus = httpStatus
    const meta = ERROR_HINTS[code] || ERROR_HINTS.INTERNAL_ERROR
    this.hint = meta.hint
    this.extra = meta.extra
    this.tone = meta.tone
    this.action = meta.action || null
  }
}

/**
 * 把任意 fetch 失败归一成 ApiError。
 * @param {any} err
 * @returns {ApiError}
 */
export function toApiError(err) {
  if (err instanceof ApiError) return err
  return new ApiError('NETWORK_ERROR', ERROR_HINTS.NETWORK_ERROR.hint, 0)
}
