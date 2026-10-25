/** 提交（判题结果 / 历史）组合式函数 */
import { ref } from 'vue'
import * as api from '../api/client.js'
import { toApiError } from '../api/errors.js'

export function useSubmission() {
  const submission = ref(null)
  const loading = ref(false)
  const error = ref(null)

  /** GET /api/submissions/:sid —— 刷新/分享链接时走此查询 */
  async function load(sid) {
    loading.value = true
    error.value = null
    submission.value = null
    try {
      submission.value = await api.getSubmission(sid)
    } catch (e) {
      error.value = toApiError(e)
    } finally {
      loading.value = false
    }
  }

  return { submission, loading, error, load }
}

export function useSubmissionList() {
  const items = ref([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref(null)

  async function load(query) {
    loading.value = true
    error.value = null
    try {
      const data = await api.getSubmissions(query)
      items.value = data.items || []
      total.value = data.total != null ? data.total : items.value.length
    } catch (e) {
      error.value = toApiError(e)
    } finally {
      loading.value = false
    }
  }

  return { items, total, loading, error, load }
}
