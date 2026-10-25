/** 题目数据组合式函数（列表 / 详情）。
 * 取数优先级：FastAPI（本地/自托管）→ 静态打包题库（GitHub Pages 无后端降级）。
 */
import { ref } from 'vue'
import * as api from '../api/client.js'
import { toApiError } from '../api/errors.js'
import bundledProblems from '../data/problems.json'

/** 静态打包题库（scripts/build-problem-data.mjs 生成；AI 评分入参同源） */
const bundled = Array.isArray(bundledProblems) ? bundledProblems : []

function fromBundled() {
  return {
    items: bundled.map((p) => ({
      id: p.id,
      title: p.title,
      contest_type: p.contest_type,
      score: p.score,
      test_count: p.test_count,
      time_limit_ms: p.limits && p.limits.time_ms,
      memory_limit_mb: p.limits && p.limits.memory_mb,
      build_mode: p.build && p.build.mode,
      topic: p.topic,
      difficulty: p.difficulty
    })),
    total: bundled.length
  }
}

function bundledDetail(pid) {
  return bundled.find((p) => p.id === pid) || null
}

/** 题目列表：加载一次后缓存在模块级，避免来回路由重复请求 */
let problemsCache = null

export function useProblems() {
  const items = ref([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref(null)

  async function load(force = false) {
    if (problemsCache && !force) {
      items.value = problemsCache.items
      total.value = problemsCache.total
      return
    }
    loading.value = true
    error.value = null
    try {
      const data = await api.getProblems()
      items.value = data.items || []
      total.value = data.total != null ? data.total : items.value.length
      problemsCache = { items: items.value, total: total.value }
    } catch (e) {
      // FastAPI 不可达（如 GitHub Pages）→ 静态题库降级
      if (bundled.length) {
        const data = fromBundled()
        items.value = data.items
        total.value = data.total
        problemsCache = { items: items.value, total: total.value }
      } else {
        error.value = toApiError(e)
      }
    } finally {
      loading.value = false
    }
  }

  return { items, total, loading, error, load }
}

export function useProblem() {
  const problem = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function load(pid) {
    loading.value = true
    error.value = null
    problem.value = null
    try {
      problem.value = await api.getProblem(pid)
    } catch (e) {
      const local = bundledDetail(pid)
      if (local) {
        problem.value = local
      } else {
        error.value = toApiError(e)
      }
    } finally {
      loading.value = false
    }
  }

  return { problem, loading, error, load }
}
