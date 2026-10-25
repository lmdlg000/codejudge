/**
 * Supabase 行 → 既有契约视图模型映射（site-spec 13.2 映射表 + ΔAI 异步状态流）。
 * 渲染组件复用，字段名不改；problem_title 由前端静态题库映射（云端不存）。
 * 同步判题行：status 恒 finished；异步 AI 流行：status = judging|ai_scored|pending_review|human_reviewed。
 */

/**
 * timestamptz → ISO 8601 本地秒级（YYYY-MM-DDTHH:mm:ss）。
 * @param {string} s
 */
export function toLocalIso(s) {
  if (!s) return ''
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return String(s)
  const p = (n) => String(n).padStart(2, '0')
  return (
    `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}` +
    `T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
  )
}

/**
 * 云端行 → SubmissionResult（详情页）。
 * @param {any} row submissions 表一行
 * @param {Record<string,string>} [titleMap] problem_id → problem_title
 */
export function mapCloudResult(row, titleMap = {}) {
  const cases = row.cases || []
  const asyncStatus = ['judging', 'ai_scored', 'pending_review'].includes(row.status) ||
    (typeof row.status === 'string' && row.status.startsWith('human_reviewed'))
  const asyncFlow = asyncStatus && cases.length === 0
  return {
    submission_id: row.id,
    problem_id: row.problem_id,
    problem_title: titleMap[row.problem_id] || row.problem_id,
    mode: row.mode || 'oi',
    created_at: toLocalIso(row.created_at),
    // 异步流行 status 驱动四态视图；旧同步行恒 finished
    status: asyncFlow ? row.status : 'finished',
    verdict: row.verdict,
    summary: row.summary,
    cases,
    build_log: row.build_log != null ? row.build_log : null,
    files: row.files || [],
    message: null,
    // 云内结果恒为已同步
    synced: true,
    // ΔAI 异步流字段（同步行均为 null）
    ai_score: row.score != null ? Number(row.score) : null,
    ai_confidence: row.ai_confidence != null ? Number(row.ai_confidence) : null,
    ai_feedback: row.ai_feedback || '',
    reviewed_feedback: row.reviewed_feedback || '',
    reviewed_at: row.reviewed_at ? toLocalIso(row.reviewed_at) : '',
    scored_at: row.scored_at ? toLocalIso(row.scored_at) : '',
    // ΔJudge0：真实运行数据（用例状态/stdout/stderr）
    run_summary: row.run_summary || null,
    asyncFlow
  }
}

/**
 * 云端行 → SubmissionSummary（历史列表）。
 * @param {any} row
 * @param {Record<string,string>} [titleMap]
 */
export function mapCloudSummary(row, titleMap = {}) {
  const asyncStatus = ['judging', 'ai_scored', 'pending_review'].includes(row.status) ||
    (typeof row.status === 'string' && row.status.startsWith('human_reviewed'))
    ? row.status
    : ''
  return {
    submission_id: row.id,
    problem_id: row.problem_id,
    problem_title: titleMap[row.problem_id] || row.problem_id,
    created_at: toLocalIso(row.created_at),
    mode: row.mode || 'oi',
    verdict: row.verdict,
    // 异步流无 summary：AI 有分时合成 score/max_score 供列表得分列显示
    summary:
      row.summary ||
      (asyncStatus && row.score != null
        ? { passed: null, total: null, pass_rate: 0, score: Number(row.score), max_score: 100, partial_score: 0 }
        : null),
    file_label: row.file_label || '',
    // ΔAI：异步流状态（同步行为空串）
    async_status: asyncStatus
  }
}

/**
 * 云端行列表 → SubmissionSummary[]。
 * @param {any[]} rows
 * @param {Record<string,string>} [titleMap]
 */
export function mapCloudSummaries(rows, titleMap = {}) {
  return (rows || []).map((r) => mapCloudSummary(r, titleMap))
}
