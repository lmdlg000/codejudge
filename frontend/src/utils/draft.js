/**
 * 草稿持久化 —— 刷新/误关页面后编辑器内容不丢。
 * 选型：localStorage（纯功能存储，非跟踪 Cookie，无需同意弹窗）；
 * 站点已有 localStorage 用法（App.vue 提示条关闭态），不引入新合规面。
 * 读写均 try/catch：隐私模式/禁用存储时静默降级为不持久化。
 */
const PREFIX = 'codejudge-draft-'

/** 草稿 TTL：30 天未碰自动作废，避免永久残留 */
const TTL_MS = 30 * 24 * 3600 * 1000

/**
 * 读草稿。@param {string} pid @returns {{mode?:string, code?:string, files?:{name:string,content:string}[]}|null}
 */
export function loadDraft(pid) {
  if (!pid) return null
  try {
    const raw = localStorage.getItem(PREFIX + pid)
    if (!raw) return null
    const data = JSON.parse(raw)
    if (!data || typeof data !== 'object') return null
    if (data.savedAt && Date.now() - data.savedAt > TTL_MS) {
      localStorage.removeItem(PREFIX + pid)
      return null
    }
    return data
  } catch {
    return null
  }
}

/** 写草稿（防抖后落盘即可，单次写入开销很小） */
export function saveDraft(pid, draft) {
  if (!pid) return
  try {
    localStorage.setItem(PREFIX + pid, JSON.stringify({ ...draft, savedAt: Date.now() }))
  } catch {
    /* 存储不可用/超限时静默放弃持久化 */
  }
}

/** 清草稿（如需显式「清空编辑器」入口时调用） */
export function clearDraft(pid) {
  if (!pid) return
  try {
    localStorage.removeItem(PREFIX + pid)
  } catch {
    /* ignore */
  }
}
