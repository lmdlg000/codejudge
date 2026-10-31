<script setup>
/**
 * 页面 4：提交历史 `/submissions`。
 * Δ2-4 双数据源：supabase 模式双 tab「云端 · 按账号隔离」|「本机 · reports/」；
 * 未配置 = 现状全站行为不变（不渲染 tab，只走 reports/）。
 * 倒序列表 + 按题目/判定筛选（URL query 同步）+ 三种空状态文案逐字（Δ1-4）。
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HistoryTable from '../components/HistoryTable.vue'
import ErrorBar from '../components/ErrorBar.vue'
import EmptyState from '../components/EmptyState.vue'
import AppButton from '../components/AppButton.vue'
import AppTabs from '../components/AppTabs.vue'
import { useSubmissionList } from '../composables/useSubmission.js'
import { useProblems } from '../composables/useProblems.js'
import {
  effectiveAuthMode,
  isLoggedIn
} from '../composables/useAuth.js'
import { supabase } from '../api/supabase.js'
import { getSubmissions, getSubmission } from '../api/client.js'
import { toApiError } from '../api/errors.js'
import { mapCloudSummaries } from '../utils/cloudMap.js'
import { TDK_HISTORY, applyTdk } from '../utils/tdk.js'
import { formatNum, formatPercent } from '../utils/format.js'
import { VERDICTS } from '../utils/verdicts.js'

/** 异步 AI 流状态（供筛选下拉） */
const ASYNC_STATUSES = [
  { value: 'human_reviewed_pass', label: '复核通过' },
  { value: 'human_reviewed_fail', label: '复核不通过' },
  { value: 'ai_scored', label: 'AI 初评' },
  { value: 'pending_review', label: '待人工确认' },
  { value: 'judging', label: '评分中' }
]

const route = useRoute()
const router = useRouter()

const { items, total, loading, error, load } = useSubmissionList()
const { items: problems, load: loadProblems } = useProblems()

const LIMIT = 20
const offset = ref(0)
const filterProblem = ref('')
const filterVerdict = ref('') // 客户端展示筛选（API 仅支持 problem_id）

const loadedOnce = ref(false)

/* —— 双 tab（Δ2-4）—— */
const activeTab = ref('local') // cloud | local
const showTabs = computed(() => effectiveAuthMode.value)

const sourceTabs = [
  { key: 'cloud', label: '云端 · 按账号隔离' },
  { key: 'local', label: '本机 · reports/' }
]

/* —— 云端数据 —— */
const cloudItems = ref([])
const cloudTotal = ref(0)
const cloudLoading = ref(false)
const cloudError = ref(null)
const cloudLoaded = ref(false)

/** 当前 tab 的列表（筛选后） */
const visibleItems = computed(() => {
  const list = activeTab.value === 'cloud' ? cloudItems.value : items.value
  if (!filterVerdict.value) return list
  return list.filter(
    (it) => it.verdict === filterVerdict.value || it.async_status === filterVerdict.value
  )
})

const hasFilter = computed(() => !!(filterProblem.value || filterVerdict.value))

/** 行得分（异步取 ai_score/summary.score，同步取 summary.score） */
function rowScore(it) {
  if (it.summary && it.summary.score != null) return Number(it.summary.score)
  if (it.ai_score != null) return Number(it.ai_score)
  return null
}

/** 统计行：共 {total} 次评测 + 平均分 + 代码质量评级 */
const statsText = computed(() => {
  const scores = visibleItems.value.map(rowScore).filter((s) => s != null)
  const base = activeTab.value === 'cloud' ? cloudTotal.value : total.value
  if (!scores.length) return `共 ${formatNum(base)} 次评测 · 暂无评分`
  const avg = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
  const grade = avg >= 90 ? 'A' : avg >= 80 ? 'B' : avg >= 70 ? 'C' : avg >= 60 ? 'D' : 'F'
  return `共 ${formatNum(base)} 次评测 · 平均分 ${avg}/100 · 质量评级 ${grade}`
})

const statsTip =
  '平均分 = 有分数提交的得分均值；质量评级：A ≥ 90，B ≥ 80，C ≥ 70，D ≥ 60，F < 60。提交须先通过样例，故低分提交通常不会出现。'

const canLoadMore = computed(() => {
  const len = activeTab.value === 'cloud' ? cloudItems.value.length : items.value.length
  const t = activeTab.value === 'cloud' ? cloudTotal.value : total.value
  return len < t
})

function titleMap() {
  const m = {}
  problems.value.forEach((p) => {
    m[p.id] = p.title
  })
  return m
}

function syncQuery() {
  const q = {}
  if (filterProblem.value) q.problem_id = filterProblem.value
  if (filterVerdict.value) q.verdict = filterVerdict.value
  if (showTabs.value) q.tab = activeTab.value
  router.replace({ query: q })
}

async function fetchList(reset) {
  if (reset) offset.value = 0
  const query = { limit: LIMIT, offset: offset.value }
  if (filterProblem.value) query.problem_id = filterProblem.value
  await load(query)
  loadedOnce.value = true
}

/** 云端列表（RLS 按用户隔离，再过滤一次） */
async function fetchCloud(reset) {
  if (!effectiveAuthMode.value || !supabase || !isLoggedIn.value) return
  if (reset) offset.value = 0
  cloudLoading.value = true
  cloudError.value = null
  try {
    await loadProblems()
    let q = supabase
      .from('submissions')
      .select('*', { count: 'exact' })
      .order('created_at', { ascending: false })
      .range(offset.value, offset.value + LIMIT - 1)
    if (filterProblem.value) q = q.eq('problem_id', filterProblem.value)
    const { data, error: qerr, count } = await q
    if (qerr) throw qerr
    const mapped = mapCloudSummaries(data || [], titleMap())
    cloudItems.value = reset ? mapped : cloudItems.value.concat(mapped)
    cloudTotal.value = count != null ? count : cloudItems.value.length
    cloudLoaded.value = true
  } catch (e) {
    cloudError.value = toApiError(e)
  } finally {
    cloudLoading.value = false
  }
}

function onFilterChange() {
  syncQuery()
  if (activeTab.value === 'cloud') fetchCloud(true)
  else fetchList(true)
}

function clearFilter() {
  filterProblem.value = ''
  filterVerdict.value = ''
  syncQuery()
  if (activeTab.value === 'cloud') fetchCloud(true)
  else fetchList(true)
}

function onTabChange(key) {
  activeTab.value = key
  syncQuery()
  if (key === 'cloud') {
    if (!cloudLoaded.value) fetchCloud(true)
  } else if (!loadedOnce.value) {
    fetchList(true)
  }
}

async function loadMore() {
  offset.value += LIMIT
  if (activeTab.value === 'cloud') {
    fetchCloud(false)
    return
  }
  const query = { limit: LIMIT, offset: offset.value }
  if (filterProblem.value) query.problem_id = filterProblem.value
  // 追加模式：手动合并（composable.load 是整表替换）
  try {
    loading.value = true
    const data = await getSubmissions(query)
    items.value = items.value.concat(data.items || [])
    total.value = data.total != null ? data.total : items.value.length
  } catch (e) {
    error.value = toApiError(e)
  } finally {
    loading.value = false
  }
}

function openRow(sid) {
  router.push(`/submissions/${sid}`)
}

/** 「看 JSON」：拉取该次提交全量结果并下载为 JSON（不新增接口） */
async function openJson(sid) {
  try {
    let data
    if (activeTab.value === 'cloud' && effectiveAuthMode.value && isLoggedIn.value && supabase) {
      const { data: row, error: qerr } = await supabase
        .from('submissions')
        .select('*')
        .eq('id', sid)
        .maybeSingle()
      if (!qerr && row) {
        const { mapCloudResult } = await import('../utils/cloudMap.js')
        data = mapCloudResult(row, titleMap())
      }
    }
    if (!data) data = await getSubmission(sid)
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json;charset=utf-8'
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${sid}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = toApiError(e)
  }
}

/** 云端 tab 的行来源徽章 */
const rowSource = computed(() => (showTabs.value ? activeTab.value : ''))

onMounted(() => {
  applyTdk(TDK_HISTORY)
  // URL query → 筛选初值
  filterProblem.value = String(route.query.problem_id || '')
  filterVerdict.value = String(route.query.verdict || '')
  // 默认 tab：已登录云端；未登录 / 本地匿名模式本机（Δ1-4）
  if (effectiveAuthMode.value) {
    const qTab = String(route.query.tab || '')
    if (qTab === 'cloud' || qTab === 'local') activeTab.value = qTab
    else activeTab.value = isLoggedIn.value ? 'cloud' : 'local'
    if (activeTab.value === 'cloud') fetchCloud(true)
    else fetchList(true)
  } else {
    activeTab.value = 'local'
    fetchList(true)
  }
})

watch(
  () => route.query,
  (q) => {
    const p = String(q.problem_id || '')
    const v = String(q.verdict || '')
    if (p !== filterProblem.value || v !== filterVerdict.value) {
      filterProblem.value = p
      filterVerdict.value = v
      if (activeTab.value === 'cloud') fetchCloud(true)
      else fetchList(true)
    }
  }
)
</script>

<template>
  <main class="page">
    <div class="page__main container container--wide">
      <h1>这台机器上的每一次评测，都在这里</h1>

      <!-- 数据源双 tab（仅 supabase 模式渲染；local 模式保持现状） -->
      <AppTabs
        v-if="showTabs"
        v-model="activeTab"
        :tabs="sourceTabs"
        aria-label="数据源"
        class="source-tabs"
        @update:model-value="onTabChange"
      />

      <!-- 筛选条 -->
      <section class="filter" aria-label="筛选">
        <div class="filter__controls">
          <label class="filter__field">
            <span class="filter__label">题目</span>
            <select v-model="filterProblem" class="filter__select" @change="onFilterChange">
              <option value="">全部</option>
              <option v-for="p in problems" :key="p.id" :value="p.id">{{ p.id }} {{ p.title }}</option>
            </select>
          </label>
          <label class="filter__field">
            <span class="filter__label">判定</span>
            <select v-model="filterVerdict" class="filter__select" @change="onFilterChange">
              <option value="">全部</option>
              <optgroup label="同步判定">
                <option v-for="v in VERDICTS" :key="v" :value="v">{{ v }}</option>
              </optgroup>
              <optgroup label="AI 异步流">
                <option v-for="s in ASYNC_STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
              </optgroup>
            </select>
          </label>
        </div>
        <p class="filter__stats caption" :title="statsTip">
          <span class="mono-data">{{ statsText }}</span>
        </p>
      </section>

      <!-- ========== 云端 tab ========== -->
      <template v-if="activeTab === 'cloud'">
        <!-- 未登录查看云端 tab -->
        <EmptyState
          v-if="!isLoggedIn"
          illustration="inbox"
          illustration-title="登录后查看云端历史示意"
          text="登录后可查看云端历史。云端历史按账号隔离。"
          action-label="去登录"
          @action="router.push({ path: '/login', query: { redirect: '/submissions?tab=cloud' } })"
        />

        <p v-else-if="cloudLoading && !cloudLoaded" class="caption" aria-live="polite">提交记录加载中…</p>

        <ErrorBar v-else-if="cloudError" :error="cloudError" />

        <!-- 已登录、云端无记录 -->
        <EmptyState
          v-else-if="cloudLoaded && !cloudItems.length && !hasFilter"
          illustration="inbox"
          illustration-title="云端还没有评测记录示意"
          text="云端还没有评测记录。提交一份代码后，这里会出现每一次的判定与得分。"
          action-label="去做 P1"
          @action="router.push('/problems/P1')"
        />

        <!-- 筛选无结果 -->
        <EmptyState
          v-else-if="cloudLoaded && !visibleItems.length && hasFilter"
          illustration="inbox"
          illustration-title="筛选无结果示意"
          text="该题目下还没有提交记录。换个题目或看全部。"
          action-label="看全部"
          @action="clearFilter"
        />

        <template v-else-if="cloudLoaded">
          <HistoryTable :items="visibleItems" :source="rowSource" @open="openRow" @json="openJson" />
          <div v-if="canLoadMore" class="more">
            <AppButton variant="secondary" :disabled="cloudLoading" @click="loadMore">
              {{ cloudLoading ? '加载中…' : '加载更多' }}
            </AppButton>
          </div>
        </template>
      </template>

      <!-- ========== 本机 tab（= 现状行为） ========== -->
      <template v-else>
        <p v-if="loading && !loadedOnce" class="caption" aria-live="polite">提交记录加载中…</p>

        <ErrorBar v-else-if="error" :error="error" />

        <!-- 无提交历史（本机 tab 空状态沿用既有文案） -->
        <EmptyState
          v-else-if="loadedOnce && !items.length && !hasFilter"
          illustration="inbox"
          illustration-title="还没有评测记录的空收件箱示意"
          text="还没有评测记录。提交一份代码后，这里会出现每一次的判定与得分。"
          action-label="去做 P1"
          @action="router.push('/problems/P1')"
        />

        <!-- 筛选无结果 -->
        <EmptyState
          v-else-if="loadedOnce && !visibleItems.length && hasFilter"
          illustration="inbox"
          illustration-title="筛选无结果示意"
          text="该题目下还没有提交记录。换个题目或看全部。"
          action-label="看全部"
          @action="clearFilter"
        />

        <template v-else-if="loadedOnce">
          <HistoryTable :items="visibleItems" :source="rowSource" @open="openRow" @json="openJson" />
          <div v-if="canLoadMore" class="more">
            <AppButton variant="secondary" :disabled="loading" @click="loadMore">
              {{ loading ? '加载中…' : '加载更多' }}
            </AppButton>
          </div>
        </template>
      </template>
    </div>
  </main>
</template>

<style scoped>
.source-tabs {
  margin: var(--space-5) 0 0;
  max-width: 420px;
}

.filter {
  margin: var(--space-5) 0 var(--space-4);
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.filter__controls {
  display: flex;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.filter__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.filter__label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.filter__select {
  height: var(--control-h);
  min-width: 160px;
  padding: 0 var(--space-3);
  border: var(--border-strong);
  border-radius: var(--radius);
  background: var(--bg-surface);
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
}

.filter__select:hover {
  border-color: var(--text-muted);
}

.filter__select:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
  border-color: var(--primary);
}

.filter__stats {
  color: var(--text-secondary);
  margin-left: auto;
}

.more {
  margin-top: var(--space-5);
  display: flex;
  justify-content: center;
}

@media (max-width: 640px) {
  .filter {
    flex-direction: column;
    align-items: stretch;
  }

  .filter__stats {
    margin-left: 0;
  }
}
</style>
