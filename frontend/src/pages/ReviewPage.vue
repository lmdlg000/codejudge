<script setup>
/**
 * 人工复核页 `/review`（ΔAI 异步流）。
 * 数据源：human_review_queue（status=pending）+ 对应 submissions 行；
 * 复核完成走 RPC complete_review（security definer，reviewers 白名单校验）。
 * 非复核人 select 为空 / RPC 报 not a reviewer → 显示无权限空态。
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../api/supabase.js'
import { effectiveAuthMode, isLoggedIn, accessToken } from '../composables/useAuth.js'
import { submitReview } from '../api/asyncSubmit.js'
import AppButton from '../components/AppButton.vue'
import AppTabs from '../components/AppTabs.vue'
import SourceEcho from '../components/SourceEcho.vue'
import ErrorBar from '../components/ErrorBar.vue'
import EmptyState from '../components/EmptyState.vue'
import { toApiError } from '../api/errors.js'
import { toLocalIso } from '../utils/cloudMap.js'
import { formatDateTime } from '../utils/format.js'
import { TDK_ABOUT, applyTdk } from '../utils/tdk.js'

const router = useRouter()
const items = ref([])
const loading = ref(true)
const error = ref(null)
const notReviewer = ref(false)
const submittingId = ref('')

/** 每行的复核表单（score / feedback） */
const forms = ref({})

const pendingCount = computed(() => items.value.length)

async function init() {
  loading.value = true
  error.value = null
  notReviewer.value = false
  applyTdk({
    title: '人工复核 · CodeJudge',
    description: '复核 AI 低置信度提交，确认最终得分与反馈。'
  })
  if (!effectiveAuthMode.value || !isLoggedIn.value || !supabase) {
    loading.value = false
    notReviewer.value = true
    return
  }
  try {
    const { data: queue, error: qerr } = await supabase
      .from('human_review_queue')
      .select('*')
      .eq('status', 'pending')
      .order('created_at', { ascending: true })
    if (qerr) throw Object.assign(new Error(qerr.message), { code: 'INTERNAL_ERROR' })
    if (!queue || queue.length === 0) {
      items.value = []
      loading.value = false
      return
    }
    const ids = queue.map((q) => q.submission_id)
    const { data: rows, error: serr } = await supabase
      .from('submissions')
      .select('*')
      .in('id', ids)
    if (serr) throw Object.assign(new Error(serr.message), { code: 'INTERNAL_ERROR' })
    const byId = {}
    ;(rows || []).forEach((r) => {
      byId[r.id] = r
    })
    items.value = queue
      .filter((q) => byId[q.submission_id])
      .map((q) => ({ queue: q, sub: byId[q.submission_id] }))
    const initForms = {}
    items.value.forEach(({ queue: q }) => {
      initForms[q.submission_id] = {
        score: q.ai_score != null ? String(q.ai_score) : '85',
        feedback: q.ai_feedback || '',
        decision: 'pass'
      }
    })
    forms.value = initForms
  } catch (e) {
    error.value = toApiError(e)
  } finally {
    loading.value = false
  }
}

async function completeReview(submissionId) {
  const f = forms.value[submissionId]
  if (!f || submittingId.value) return
  const score = Number(f.score)
  if (!Number.isFinite(score) || score < 0 || score > 100) {
    error.value = toApiError({
      code: 'VALIDATION_ERROR',
      message: '提交内容不合法，请检查后重试：分数须为 0–100 的数字'
    })
    return
  }
  submittingId.value = submissionId
  error.value = null
  try {
    // admin-review Edge Function：JWT + reviewers 白名单 + secret 收队列改状态
    const res = await submitReview(
      {
        submission_id: submissionId,
        score,
        feedback: String(f.feedback || ''),
        decision: f.decision === 'fail' ? 'fail' : 'pass'
      },
      accessToken()
    )
    if (res && res.status && res.status.startsWith('human_reviewed')) {
      items.value = items.value.filter((it) => it.queue.submission_id !== submissionId)
    }
  } catch (e) {
    const err = toApiError(e)
    if (err.code === 'UNAUTHORIZED' && /复核权限/.test(err.message || '')) {
      notReviewer.value = true
      return
    }
    error.value = err
  } finally {
    submittingId.value = ''
  }
}

/** 该提交的 UAPI 运行数据（裁决参考） */
function runCasesOf(sub) {
  const rs = sub && sub.run_summary
  return (rs && rs.cases) || []
}

onMounted(init)
</script>

<template>
  <main class="page">
    <div class="page__main container">
      <h1>人工复核队列</h1>
      <p class="caption review-lead">
        AI 置信度不足或评分失败的提交会进入本队列。复核后状态经 Realtime 推送为「复核完成」。
      </p>

      <p v-if="loading" class="caption" aria-live="polite">复核队列加载中…</p>

      <ErrorBar v-else-if="error" :error="error" />

      <EmptyState
        v-else-if="notReviewer"
        illustration="wrench"
        illustration-title="无复核权限示意"
        text="当前账号不在复核人名单中。请让管理员把你的账号加入 reviewers 表后重试。"
        action-label="回到题目列表"
        @action="router.push('/')"
      />

      <EmptyState
        v-else-if="!pendingCount"
        illustration="inbox"
        illustration-title="空复核队列示意"
        text="复核队列为空。AI 置信度不足的提交会自动出现在这里。"
        action-label="回到题目列表"
        @action="router.push('/')"
      />

      <ul v-else class="review-list">
        <li v-for="it in items" :key="it.queue.submission_id" class="review-card">
          <div class="review-card__head">
            <span class="mono-data">{{ it.queue.submission_id }}</span>
            <span class="review-card__pid">{{ it.sub.problem_id }}</span>
            <span class="review-card__reason mono-data">{{ it.queue.reason === 'ai_failed' ? 'AI 评分失败' : it.queue.reason === 'low_score' ? '分数偏低' : it.queue.reason === 'bad_data' ? '数据问题重审' : it.queue.reason === 'force_submit' ? '样例未全过强制提交' : '无法可靠判断' }}</span>
            <span
              v-if="it.queue.priority === 'high'"
              class="review-card__reason mono-data review-card__reason--high"
            >高优先</span>
            <span class="caption">{{ formatDateTime(toLocalIso(it.queue.created_at)) }}</span>
          </div>

          <p class="review-card__ai mono-data">
            AI 初评：{{ it.queue.ai_score != null ? `${it.queue.ai_score} / 100` : '无' }}
            <span v-if="it.queue.ai_confidence != null" class="caption">
              · 置信度 {{ Math.round(it.queue.ai_confidence * 100) }}%
            </span>
          </p>
          <p v-if="it.queue.ai_feedback" class="review-card__fb">{{ it.queue.ai_feedback }}</p>

          <!-- Judge0 真实运行数据（裁决参考） -->
          <div v-if="runCasesOf(it.sub).length" class="review-card__run">
            <p class="caption review-card__run-title">UAPI 运行数据</p>
            <ul class="review-card__runs">
              <li v-for="c in runCasesOf(it.sub)" :key="c.case" class="mono-data">
                #{{ c.case }} {{ c.status }}
                <span v-if="c.time_ms != null">· {{ c.time_ms }}ms</span>
                · 期望 {{ JSON.stringify(c.expected).slice(0, 48) }}
                · 实际 {{ JSON.stringify(c.actual).slice(0, 48) }}
              </li>
            </ul>
          </div>

          <SourceEcho :files="it.sub.files || []" class="review-card__code" />

          <div class="review-card__form">
            <label class="review-card__label">
              最终得分
              <input
                v-model="forms[it.queue.submission_id].score"
                class="review-card__input mono-data"
                type="number"
                min="0"
                max="100"
                step="1"
              />
            </label>
            <label class="review-card__label">
              裁决
              <select v-model="forms[it.queue.submission_id].decision" class="review-card__input">
                <option value="pass">通过</option>
                <option value="fail">未通过</option>
                <option value="bad_data">数据问题（退回重审）</option>
              </select>
            </label>
            <label class="review-card__label review-card__label--grow">
              复核反馈
              <textarea
                v-model="forms[it.queue.submission_id].feedback"
                class="review-card__textarea"
                rows="2"
                placeholder="留给用户的最终反馈"
              ></textarea>
            </label>
            <AppButton
              variant="primary"
              :loading="submittingId === it.queue.submission_id"
              @click="completeReview(it.queue.submission_id)"
            >确认复核</AppButton>
          </div>
        </li>
      </ul>
    </div>
  </main>
</template>

<style scoped>
.review-lead {
  margin: var(--space-3) 0 var(--space-6);
  color: var(--text-secondary);
}

.review-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.review-card {
  border: var(--border);
  border-left: 4px solid var(--warning-border);
  background: var(--bg-surface);
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.review-card__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.review-card__pid {
  color: var(--primary);
  font-family: var(--font-mono);
  font-size: var(--text-mono-data);
}

.review-card__reason--high {
  color: var(--danger-text);
  border-color: var(--danger-border);
}

.review-card__reason {
  color: var(--warning-text);
  border: 1px solid var(--warning-border);
  border-radius: var(--radius-sm);
  padding: 1px 6px;
  font-size: var(--text-micro);
}

.review-card__ai {
  margin: 0;
  color: var(--text-primary);
}

.review-card__fb {
  margin: 0;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.review-card__run {
  border: var(--border);
  background: var(--code-bg);
  padding: var(--space-3);
}

.review-card__run-title {
  margin: 0 0 var(--space-2);
  color: var(--code-muted);
}

.review-card__runs {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--code-text);
  font-size: var(--text-micro);
  overflow-x: auto;
}

.review-card__form {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: flex-end;
}

.review-card__label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: var(--text-caption);
  color: var(--text-secondary);
}

.review-card__label--grow {
  flex: 1;
  min-width: 220px;
}

.review-card__input {
  width: 96px;
  height: var(--control-h);
  padding: 0 var(--space-2);
  background: var(--code-bg);
  border: 1px solid var(--code-border);
  border-radius: var(--radius-sm);
  color: var(--code-text);
}

.review-card__textarea {
  width: 100%;
  padding: var(--space-2);
  background: var(--code-bg);
  border: 1px solid var(--code-border);
  border-radius: var(--radius-sm);
  color: var(--code-text);
  font-family: var(--font-mono);
  font-size: var(--text-mono-code);
  resize: vertical;
}
</style>
