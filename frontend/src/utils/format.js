/**
 * 展示格式化 —— 数字/日期/横幅片段。
 * 得分横幅格式逐字冻结：通过 {passed}/{total} · 通过率 {rate}% · 得分 {score}/{max_score}
 */

/**
 * ISO 8601 → 展示用 `YYYY-MM-DD HH:MM:SS`（本地、秒级）。
 * @param {string} iso
 */
export function formatDateTime(iso) {
  if (!iso) return '—'
  // 契约为无时区 ISO（如 2025-01-01T12:00:00），按本地直读避免时区换算
  const m = String(iso).match(
    /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})/
  )
  if (m) return `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}:${m[6]}`
  return String(iso)
}

/**
 * 数字展示：整数不带小数，浮点最多 2 位并去尾零。
 * @param {number|null|undefined} n
 */
export function formatNum(n) {
  if (n == null || Number.isNaN(n)) return '—'
  const r = Math.round(n * 100) / 100
  return Number.isInteger(r) ? String(r) : String(r)
}

/**
 * 通过率展示：契约 pass_rate 为 0–1（4 位小数），横幅显示百分比。
 * @param {number} rate
 */
export function formatPercent(rate) {
  if (rate == null || Number.isNaN(rate)) return '—'
  const pct = rate * 100
  const r = Math.round(pct * 100) / 100
  return Number.isInteger(r) ? String(r) : String(r)
}

/**
 * 得分横幅三段（seg）文本 —— 句式冻结，不得改字。
 * @param {import('../api/types.js').Summary} s
 */
export function bannerSegments(s) {
  return {
    passed: `通过 ${formatNum(s.passed)}/${formatNum(s.total)}`,
    rate: `通过率 ${formatPercent(s.pass_rate)}%`,
    score: `得分 ${formatNum(s.score)}/${formatNum(s.max_score)}`
  }
}

/**
 * 横幅补充行（mode 与结果二选一，文案取 content-plan）。
 * @param {'acm'|'oi'} mode
 * @param {import('../api/types.js').Summary} s
 */
export function bannerNote(mode, s) {
  if (mode === 'oi') return 'OI 模式：按通过用例的权重折算得分。'
  const allPass = s.total > 0 && s.passed === s.total
  if (allPass) return 'ACM 模式：全部用例通过，记满分。'
  return `ACM 模式：未全对记 0 分。加权部分得分 ${formatNum(s.partial_score)}，仅供参考。`
}

/**
 * 计分模式中文（结果页「本次计分模式」）。
 * @param {'acm'|'oi'} mode
 */
export function modeLabel(mode) {
  return mode === 'oi' ? 'OI（按权重计分）' : 'ACM（全对记分）'
}

/** 卡片/标签上的短模式名 */
export function modeShort(mode) {
  return mode === 'oi' ? 'OI' : 'ACM'
}

/** 空消息占位（表格「提示」列） */
export const EM_DASH = '—'
