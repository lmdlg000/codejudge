<script setup>
/**
 * 页面 3：判题结果 `/submissions/:sid`。
 * 位置关系冻结：得分横幅第一 → CE 面板（仅 CE，置于表格之前）→ 逐用例表格
 * → RE 面板 → 源码回显（默认折叠）→ 动作条。
 * 「下载报告 JSON」= 把 GET /api/submissions/:sid 响应序列化为 JSON 文件下载（不新增接口）。
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ScoreBanner from '../components/ScoreBanner.vue'
import CaseTable from '../components/CaseTable.vue'
import BuildLogPanel from '../components/BuildLogPanel.vue'
import SourceEcho from '../components/SourceEcho.vue'
import CollapsePanel from '../components/CollapsePanel.vue'
import VerdictBadge from '../components/VerdictBadge.vue'
import ErrorBar from '../components/ErrorBar.vue'
import AlertBar from '../components/AlertBar.vue'
import EmptyState from '../components/EmptyState.vue'
import AppButton from '../components/AppButton.vue'
import SyncBadge from '../components/SyncBadge.vue'
import { useSubmission } from '../composables/useSubmission.js'
import { useProblems } from '../composables/useProblems.js'
import {
  effectiveAuthMode,
  isLoggedIn,
  accessToken
} from '../composables/useAuth.js'
import { supabase } from '../api/supabase.js'
import { watchSubmission } from '../api/asyncSubmit.js'
import * as api from '../api/client.js'
import { toApiError } from '../api/errors.js'
import { mapCloudResult } from '../utils/cloudMap.js'
import { TDK_RESULT, applyTdk } from '../utils/tdk.js'
import { formatDateTime, modeLabel, EM_DASH } from '../utils/format.js'
import { verdictMeta, reExplain, SIGNAL_MSG } from '../utils/verdicts.js'

const route = useRoute()
const router = useRouter()
const { submission, loading, error, load } = useSubmission()
const { items: problems, load: loadProblems } = useProblems()

const sid = computed(() => String(route.params.sid || ''))
const result = computed(() => submission.value)
const meta = computed(() => verdictMeta(result.value && result.value.verdict))
const isCe = computed(() => result.value && result.value.verdict === 'CE')
const isFailed = computed(() => result.value && result.value.status === 'failed')

/* ===== ΔAI 异步评分流（judging → ai_scored | pending_review → human_reviewed）===== */
const isAsync = computed(() => !!(result.value && result.value.asyncFlow))
const asyncStatus = computed(() => (isAsync.value ? result.value.status : ''))
const isHuman = computed(() => String(asyncStatus.value).startsWith('human_reviewed'))

const asyncTitle = computed(() => {
  switch (asyncStatus.value) {
    case 'judging':
      return '评分中'
    case 'ai_scored':
      return 'AI 初评完成'
    case 'pending_review':
      return 'AI 已评分，正在等待人工确认'
    case 'human_reviewed_pass':
      return '人工复核完成（通过）'
    case 'human_reviewed_fail':
      return '人工复核完成（未通过）'
    case 'human_reviewed':
      return '人工复核完成'
    default:
      return '判定结果'
  }
})

/** Judge0 真实运行数据（run_summary） */
const runCases = computed(() => {
  const rs = result.value && result.value.run_summary
  return (rs && rs.cases) || []
})
const runSkipped = computed(() => {
  const rs = result.value && result.value.run_summary
  return (rs && rs.skipped) || ''
})

/** Realtime 订阅：状态变更推送（RLS 生效；零轮询零刷新） */
let unwatch = null
function stopWatch() {
  if (unwatch) {
    unwatch()
    unwatch = null
  }
}
function startWatch() {
  stopWatch()
  if (!isAsync.value) return
  unwatch = watchSubmission(sid.value, (row) => {
    if (row) submission.value = mapCloudResult(row, titleMap())
  })
}
onUnmounted(stopWatch)

/** supabase 模式未登录看结果：空态 + 登录 CTA（契约 13.2：不发请求） */
const needLogin = ref(false)

/** 同步徽章：本次是否带过 token（POST 时记 sessionStorage；云内结果恒已同步） */
const hadToken = computed(() => {
  if (!result.value) return false
  if (result.value.synced) return true
  try {
    if (sessionStorage.getItem(`codejudge-auth-${result.value.submission_id}`)) return true
  } catch {
    /* ignore */
  }
  // 刷新场景：supabase 模式且当前已登录 → 按带过 token 处理（可重试）
  return effectiveAuthMode.value && isLoggedIn.value
})

const retrying = ref(false)

/** 本次计分模式是否覆盖了题目默认（仅提交时 sessionStorage 有记录才显示） */
const modeNote = computed(() => {
  if (!result.value) return ''
  try {
    const raw = sessionStorage.getItem(`codejudge-mode-${result.value.submission_id}`)
    if (!raw) return ''
    const info = JSON.parse(raw)
    if (info && info.defaultMode && info.mode && info.mode !== info.defaultMode) {
      return `（已覆盖题目默认 ${info.defaultMode === 'oi' ? 'OI' : 'ACM'}）`
    }
  } catch {
    /* ignore */
  }
  return ''
})

/** RE 面板数据：首个 RE 用例（signal / stderr_tail / exit_code） */
const reCase = computed(() => {
  const list = (result.value && result.value.cases) || []
  return list.find((c) => c.verdict === 'RE') || null
})
const showRePanel = computed(() => !!reCase.value)
const reText = computed(() => (reCase.value ? reExplain(reCase.value) : ''))
const reHasSignal = computed(
  () => !!(reCase.value && reCase.value.signal && SIGNAL_MSG[reCase.value.signal])
)

/** problem_id → 静态题库标题（云端不存 problem_title） */
function titleMap() {
  const m = {}
  problems.value.forEach((p) => {
    m[p.id] = p.title
  })
  return m
}

async function init() {
  needLogin.value = false
  stopWatch()

  // supabase 模式：未登录不发请求（13.2）；已登录先查云，miss 回退本地 GET
  if (effectiveAuthMode.value) {
    if (!isLoggedIn.value) {
      needLogin.value = true
      loading.value = false
      return
    }
    if (supabase) {
      loading.value = true
      error.value = null
      try {
        await loadProblems()
        const { data: row, error: qerr } = await supabase
          .from('submissions')
          .select('*')
          .eq('id', sid.value)
          .maybeSingle()
        if (!qerr && row) {
          submission.value = mapCloudResult(row, titleMap())
          loading.value = false
          applyResultTdk()
          startWatch()
          return
        }
      } catch {
        /* 落到本地 GET 回退 */
      }
      loading.value = false
    }
  }

  await load(sid.value)
  applyResultTdk()
}

function applyResultTdk() {
  if (result.value) {
    applyTdk({
      title: TDK_RESULT.title(result.value.problem_title || result.value.problem_id),
      description: TDK_RESULT.description
    })
  }
}

onMounted(init)
watch(
  () => route.params.sid,
  () => {
    if (route.name === 'submission-detail') init()
  }
)

/**
 * 重试同步（Δ2-3）：契约无独立入库接口，最轻方案 = 重带 token 再交一次
 * （同一 problem_id/files/mode 重新 POST，判题重跑，新 sid 入库后跳新结果页）。
 */
async function retrySync() {
  const data = result.value
  if (!data || retrying.value) return
  retrying.value = true
  try {
    const payload = { problem_id: data.problem_id, mode: data.mode }
    const files = data.files || []
    if (files.length === 1) {
      payload.source_code = files[0].content
      payload.filename = files[0].name
    } else {
      payload.files = files.map((f) => ({ name: f.name, content: f.content }))
    }
    const token = accessToken()
    const fresh = await api.createSubmission(payload, token)
    try {
      if (token) sessionStorage.setItem(`codejudge-auth-${fresh.submission_id}`, '1')
      sessionStorage.setItem(
        `codejudge-mode-${fresh.submission_id}`,
        JSON.stringify({ mode: fresh.mode, defaultMode: data.mode })
      )
    } catch {
      /* ignore */
    }
    router.replace(`/submissions/${fresh.submission_id}`)
  } catch (e) {
    error.value = toApiError(e)
  } finally {
    retrying.value = false
  }
}

/** 下载报告 JSON：前端把查询响应序列化为 JSON 文件 */
function downloadJson() {
  const data = result.value
  if (!data) return
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json;charset=utf-8'
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${data.submission_id}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function copyStderr() {
  if (reCase.value && reCase.value.stderr_tail) {
    navigator.clipboard.writeText(reCase.value.stderr_tail).catch(() => {})
  }
}
</script>

<template>
  <main class="page">
    <div class="page__main container container--wide">
      <p v-if="loading" class="caption" aria-live="polite">提交记录加载中…</p>

      <!-- supabase 模式未登录：空态 + 登录 CTA（不发请求） -->
      <EmptyState
        v-if="needLogin"
        illustration="inbox"
        illustration-title="登录后查看云端结果示意"
        text="登录后可查看云端历史。云端历史按账号隔离。"
        action-label="去登录"
        @action="router.push({ path: '/login', query: { redirect: route.fullPath } })"
      />

      <!-- 结果页拿不到报告 -->
      <template v-else-if="error">
        <EmptyState
          v-if="error.code === 'SUBMISSION_NOT_FOUND'"
          illustration="inbox"
          illustration-title="找不到提交记录示意"
          :text="error.hint"
          action-label="回到提交历史"
          @action="router.push('/submissions')"
        />
        <ErrorBar v-else :error="error" />
      </template>

      <template v-else-if="result">
        <!-- 面包屑 -->
        <nav class="crumb" aria-label="面包屑">
          <router-link to="/submissions">提交历史</router-link>
          <span class="crumb__sep" aria-hidden="true">/</span>
          <span class="mono-data">{{ result.submission_id }}</span>
        </nav>

        <!-- H1：异步流显示状态；同步结果显示中文全称 + 放大徽章 -->
        <div class="title-row">
          <h1>{{ isAsync ? asyncTitle : `判定结果：${meta.label}` }}</h1>
          <VerdictBadge v-if="!isAsync" :verdict="result.verdict" large />
        </div>

        <!-- 区块 0：提交信息行 + 同步徽章（Δ2-3：信息行右侧，不占横幅） -->
        <div class="info-row">
          <p class="info-line caption">
            <span class="mono-data">提交 {{ result.submission_id }}</span>
            <span class="info-line__sep" aria-hidden="true">·</span>
            <span class="mono-data">{{ formatDateTime(result.created_at) }}</span>
            <span class="info-line__sep" aria-hidden="true">·</span>
            <span>本次计分模式 {{ modeLabel(result.mode) }}</span>
            <span v-if="modeNote">{{ modeNote }}</span>
          </p>
          <SyncBadge
            :synced="!!result.synced"
            :had-token="hadToken"
            :retrying="retrying"
            @retry="retrySync"
          />
        </div>

        <!-- ΔAI 异步评分流：四态面板（评分中 → AI 初评 / 待人工确认 → 复核完成） -->
        <section v-if="isAsync" class="block async-panel" aria-live="polite">
          <h2 class="block__title">AI 评分</h2>

          <p v-if="asyncStatus === 'judging'" class="async-panel__state">
            <span class="async-panel__spin" aria-hidden="true"></span>
            评分中…（已接收，AI 评分在后台进行，无需刷新页面）
          </p>

          <template v-else>
            <p v-if="asyncStatus === 'pending_review'" class="async-panel__state">
              AI 已评分，正在等待人工确认
            </p>
            <p v-else-if="isHuman" class="async-panel__state">
              {{ asyncTitle }}
            </p>
            <p v-else class="async-panel__state">AI 初评完成</p>

            <p class="async-panel__score mono-data">
              得分 {{ result.ai_score != null ? result.ai_score : EM_DASH }} / 100
              <span v-if="result.ai_confidence != null" class="async-panel__conf">
                · 置信度 {{ Math.round(result.ai_confidence * 100) }}%
              </span>
            </p>

            <p v-if="isHuman && result.reviewed_feedback" class="async-panel__fb">
              {{ result.reviewed_feedback }}
            </p>
            <p v-else-if="result.ai_feedback" class="async-panel__fb">{{ result.ai_feedback }}</p>

            <p v-if="asyncStatus === 'ai_scored'" class="caption">
              本次为 AI 初评结果（基于 UAPI 真实运行数据）。触发人工复核时页面会自动更新，无需刷新。
            </p>
            <p v-else-if="asyncStatus === 'pending_review'" class="caption">
              复核完成后本页会自动更新为最终结果。
            </p>
          </template>
        </section>

        <!-- ΔUAPI：真实运行数据（确定性执行结果） -->
        <section v-if="isAsync && runCases.length" class="block" aria-label="真实运行数据">
          <h2 class="block__title">真实运行数据（UAPI）</h2>
          <div class="run-table-wrap">
            <table class="run-table">
              <thead>
                <tr>
                  <th scope="col">用例</th>
                  <th scope="col">状态</th>
                  <th scope="col">耗时</th>
                  <th scope="col">期望输出</th>
                  <th scope="col">实际输出</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in runCases" :key="c.case">
                  <td class="mono-data">#{{ c.case }}</td>
                  <td class="mono-data">{{ c.status }}</td>
                  <td class="mono-data">{{ c.time_ms != null ? `${c.time_ms}ms` : EM_DASH }}</td>
                  <td class="run-table__io mono-data">{{ c.expected }}</td>
                  <td class="run-table__io mono-data">{{ c.actual || EM_DASH }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
        <p v-else-if="isAsync && runSkipped === 'no_samples'" class="caption block">
          本题无样例可实跑，AI 基于代码与题面评判。
        </p>
        <p v-else-if="isAsync && runSkipped === 'not_configured'" class="caption block">
          本次未接入执行器实跑，AI 基于代码与题面评判。
        </p>

        <!-- 区块 1：得分横幅（格式冻结；异步流行由 AI 面板呈现） -->
        <ScoreBanner
          v-if="!isAsync"
          :summary="result.summary"
          :verdict="result.verdict"
          :mode="result.mode"
          :submission-id="result.submission_id"
        />

        <!-- SE / status=failed：失败原因 -->
        <AlertBar
          v-if="isFailed"
          tone="error"
          title="评测器自身异常"
          :message="result.message || '评测器自身异常，本次提交未完成判定。这不是你代码的问题——检查题目目录与 reports/ 权限后重试。'"
        >
          <div class="fail-actions">
            <AppButton variant="primary" @click="router.push(`/problems/${result.problem_id}`)">
              重试判题
            </AppButton>
            <AppButton variant="secondary" @click="router.push('/about')">
              查看使用说明
            </AppButton>
          </div>
        </AlertBar>

        <!-- 区块 3：CE 专属 —— 编译输出面板置于逐用例表之前 -->
        <BuildLogPanel
          v-if="isCe && result.build_log"
          :build-log="result.build_log"
          class="block"
        />

        <!-- 区块 2：逐用例判定表格 -->
        <section v-if="result.cases && result.cases.length" class="block" aria-label="逐用例判定">
          <h2 class="block__title">逐用例判定</h2>
          <CaseTable :cases="result.cases" />
        </section>

        <!-- 区块 4：RE 专属面板 -->
        <section v-if="showRePanel" class="block re-panel" aria-label="程序异常退出">
          <h2 class="block__title re-panel__title">程序异常退出</h2>
          <p class="re-panel__explain">
            <span v-if="reHasSignal" class="re-panel__sig">{{ reText }}</span>
            <span v-else>{{ EM_DASH }} {{ reText }}</span>
          </p>
          <CollapsePanel
            v-if="reCase && reCase.stderr_tail"
            open-label="看 stderr"
            close-label="收起 stderr"
            title="stderr 末 2KB"
            max-height="320px"
          >
            <div class="re-panel__stderr-wrap">
              <button type="button" class="re-panel__copy" @click="copyStderr">复制 stderr</button>
              <pre class="re-panel__stderr">{{ reCase.stderr_tail }}</pre>
            </div>
          </CollapsePanel>
        </section>

        <!-- 区块 5：提交源码回显（默认折叠） -->
        <SourceEcho :files="result.files || []" class="block" />

        <!-- 区块 6：动作条 -->
        <div class="actions block">
          <AppButton variant="primary" @click="router.push(`/problems/${result.problem_id}`)">
            返回题目改代码
          </AppButton>
          <AppButton variant="secondary" @click="router.push('/submissions')">
            查看提交历史
          </AppButton>
          <AppButton variant="secondary" @click="downloadJson">
            下载报告 JSON
          </AppButton>
        </div>
      </template>
    </div>
  </main>
</template>

<style scoped>
.crumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-caption);
  color: var(--text-muted);
  margin-bottom: var(--space-3);
  flex-wrap: wrap;
}

.crumb a {
  color: var(--text-muted);
}

.crumb a:hover {
  color: var(--primary);
}

.crumb__sep {
  color: var(--text-disabled);
}

.title-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.info-line {
  margin: var(--space-3) 0 var(--space-4);
  color: var(--text-secondary);
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  align-items: baseline;
}

/* 信息行 + 同步徽章（Δ2-3：徽章右缘与信息行基线对齐；窄屏换行不挤时间戳） */
.info-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin: var(--space-3) 0 var(--space-4);
}

.info-row .info-line {
  margin: 0;
}

.info-line__sep {
  color: var(--text-muted);
}

.block {
  margin-top: var(--space-6);
}

.block__title {
  margin-bottom: var(--space-3);
  font-size: var(--text-h3);
}

.re-panel {
  background: var(--bg-surface);
  border: var(--border);
  border-left: 3px solid var(--verdict-re-text);
  border-radius: var(--radius);
  padding: var(--space-5) var(--space-6);
}

.re-panel__title {
  color: var(--verdict-re-text);
  margin-bottom: var(--space-2);
}

.re-panel__explain {
  font-size: var(--text-body);
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.re-panel__stderr-wrap {
  position: relative;
}

.re-panel__copy {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  height: 24px;
  padding: 0 var(--space-2);
  border: 1px solid #334155;
  border-radius: var(--radius-sm);
  background: var(--code-bar-bg);
  color: var(--code-text);
  font-size: var(--text-micro);
  font-weight: 500;
  cursor: pointer;
}

.re-panel__copy:hover {
  background: #334155;
}

.re-panel__stderr {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  background: var(--code-bg);
  color: var(--code-text);
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-size: var(--text-mono-code);
  line-height: var(--lh-mono-code);
  max-height: 320px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.fail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-3);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-8);
}

/* ===== ΔAI 异步评分流面板 ===== */
.async-panel {
  border: var(--border);
  border-left: 4px solid var(--primary);
  background: var(--bg-surface);
  padding: var(--space-5);
}

.async-panel__state {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-body-lg);
  color: var(--text-primary);
  margin: 0;
}

.async-panel__spin {
  width: 14px;
  height: 14px;
  flex: none;
  border-radius: 50%;
  border: 2px solid rgba(61, 255, 122, 0.3);
  border-top-color: var(--primary);
  animation: async-spin 0.9s linear infinite;
}

@keyframes async-spin {
  to {
    transform: rotate(360deg);
  }
}

.async-panel__score {
  margin: var(--space-3) 0 0;
  font-size: var(--text-banner);
  color: var(--primary);
}

.async-panel__conf {
  font-size: var(--text-caption);
  color: var(--text-secondary);
}

.async-panel__fb {
  margin: var(--space-3) 0 0;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

/* ΔUAPI 真实运行数据表 */
.run-table-wrap {
  overflow-x: auto;
}

.run-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-caption);
}

.run-table th,
.run-table td {
  border: var(--border);
  padding: var(--space-2) var(--space-3);
  text-align: left;
  vertical-align: top;
}

.run-table th {
  background: var(--bg-subtle);
  color: var(--text-secondary);
  font-weight: 600;
}

.run-table__io {
  max-width: 280px;
  overflow-wrap: anywhere;
  color: var(--code-text);
  background: var(--code-bg);
}
</style>
