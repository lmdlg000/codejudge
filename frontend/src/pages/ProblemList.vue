<script setup>
/**
 * 页面 1：题目列表（首页 `/`）。
 * 红线：工具本体首屏，零营销区块。H1 + 一行引言 + 行式卡片列表 + 分页 + 页脚。
 * 文案逐字取 content-plan 页面 1。
 * 分页：题量增长后列表会拉很长，按 PAGE_SIZE（每页 10 题）分页，页码写进 `?page=`，
 * 刷新/分享/前进后退都能回到同一页；只有一页时不渲染页码条。
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ProblemCard from '../components/ProblemCard.vue'
import ErrorBar from '../components/ErrorBar.vue'
import EmptyState from '../components/EmptyState.vue'
import { useProblems } from '../composables/useProblems.js'
import { applyTdk, TDK_HOME, PROBLEM_RANGE_LABEL } from '../utils/tdk.js'

const PAGE_SIZE = 10

const route = useRoute()
const router = useRouter()
const { items, loading, error, load } = useProblems()

const listRef = ref(null)
const page = ref(1)

const pageCount = computed(() => Math.max(1, Math.ceil(items.value.length / PAGE_SIZE)))
const pagedItems = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return items.value.slice(start, start + PAGE_SIZE)
})
const rangeText = computed(() => {
  if (!items.value.length) return ''
  const from = (page.value - 1) * PAGE_SIZE + 1
  const to = Math.min(page.value * PAGE_SIZE, items.value.length)
  return `第 ${from}–${to} 题 / 共 ${items.value.length} 题`
})

/** URL 的 ?page= 是唯一真相，非法值一律回落到第 1 页 */
function readPageFromQuery() {
  const raw = Number(route.query.page)
  const n = Number.isFinite(raw) ? Math.floor(raw) : 1
  page.value = n >= 1 ? n : 1
}

function goPage(next) {
  const target = Math.min(Math.max(1, Math.floor(next) || 1), pageCount.value)
  if (target === page.value) return
  page.value = target
  router.replace({ query: { ...route.query, page: target === 1 ? undefined : String(target) } })
  // 翻页后回到列表顶部，避免停在页面中部看到"半屏空白"
  const el = listRef.value
  if (el && typeof el.scrollIntoView === 'function') {
    el.scrollIntoView({ block: 'start', behavior: 'smooth' })
  }
}

function gotoProblem(pid) {
  router.push(`/problems/${pid}`)
}

// 页码越界（题量变化/手改 URL）自动修正
watch([pageCount, () => items.value.length], () => {
  if (page.value > pageCount.value) goPage(pageCount.value)
})
watch(() => route.query.page, readPageFromQuery)

onMounted(() => {
  applyTdk(TDK_HOME)
  readPageFromQuery()
  load()
})
</script>

<template>
  <main class="page">
    <div class="page__main container container--wide">
      <!-- H1 区压缩，保证首屏露出列表 -->
      <header class="intro">
        <h1>{{ PROBLEM_RANGE_LABEL }} 题目列表</h1>
        <p class="intro__lead">
          本地判题引擎逐用例评测，支持 ACM / OI 两种计分。点卡片进详情，写完代码即可提交判题。
        </p>
      </header>

      <!-- 工具本体：题目卡片列表 -->
      <section ref="listRef" class="list page__section" aria-label="题目列表">
        <p v-if="loading" class="list__loading caption" aria-live="polite">题目加载中…</p>

        <ErrorBar v-else-if="error" :error="error" />

        <EmptyState
          v-else-if="!items.length"
          illustration="puzzle"
          illustration-title="题目数据缺失示意图"
          text="题目数据没读出来：检查 problems/<id>/problem.json 与 tests/ 目录是否完整（每个 .in 必须有同名 .out）。"
          action-label="回到题目列表"
          @action="load(true)"
        />

        <template v-else>
          <ul class="list__items">
            <li v-for="p in pagedItems" :key="p.id" class="list__item">
              <ProblemCard :problem="p" @click="gotoProblem(p.id)" />
            </li>
          </ul>

          <nav v-if="pageCount > 1" class="pager" aria-label="题目列表分页">
            <div class="pager__group">
              <button
                type="button"
                class="pager__step mono-data"
                :disabled="page === 1"
                @click="goPage(page - 1)"
              >[ ← 上一页 ]</button>

              <ul class="pager__nums">
                <li v-for="n in pageCount" :key="n">
                  <button
                    type="button"
                    class="pager__num mono-data"
                    :class="{ 'pager__num--current': n === page }"
                    :aria-current="n === page ? 'page' : undefined"
                    :aria-label="`第 ${n} 页`"
                    @click="goPage(n)"
                  >{{ n }}</button>
                </li>
              </ul>
            </div>

            <div class="pager__group pager__group--end">
              <span class="pager__pos mono-data">{{ rangeText }}</span>
              <button
                type="button"
                class="pager__step mono-data"
                :disabled="page === pageCount"
                @click="goPage(page + 1)"
              >[ 下一页 → ]</button>
            </div>
          </nav>
        </template>
      </section>
    </div>
  </main>
</template>

<style scoped>
.intro {
  max-width: 720px;
}

.intro__lead {
  margin-top: var(--space-3);
  font-size: var(--text-body-lg);
  line-height: var(--lh-body-lg);
  color: var(--text-secondary);
}

.list {
  margin-top: var(--space-8);
  scroll-margin-top: 88px;
}

.list__loading {
  color: var(--text-secondary);
}

.list__items {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.pager {
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.pager__group {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.pager__group--end {
  gap: var(--space-4);
}

.pager__step {
  font-size: var(--text-micro);
  color: var(--primary);
  background: transparent;
  border: 1px solid var(--code-border);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  cursor: pointer;
  transition: background 120ms ease, color 120ms ease;
}

.pager__step:hover:not(:disabled) {
  background: var(--bg-subtle);
}

.pager__step:disabled {
  color: var(--text-muted);
  cursor: not-allowed;
  opacity: 0.6;
}

.pager__nums {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  gap: var(--space-1);
}

.pager__num {
  min-width: 32px;
  height: 32px;
  padding: 0 6px;
  font-size: var(--text-micro);
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.pager__num:hover {
  border-color: var(--neutral-200);
  color: var(--text-primary);
}

.pager__num--current,
.pager__num--current:hover {
  color: var(--text-inverse);
  background: var(--primary);
  border-color: var(--primary);
  font-weight: 700;
  cursor: default;
}

.pager__pos {
  font-size: var(--text-micro);
  color: var(--text-muted);
  white-space: nowrap;
}

@media (max-width: 640px) {
  .pager {
    justify-content: center;
  }

  .pager__group,
  .pager__group--end {
    width: 100%;
    justify-content: center;
  }
}
</style>
