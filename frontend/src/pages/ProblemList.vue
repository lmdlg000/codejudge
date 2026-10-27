<script setup>
/**
 * 页面 1：题目列表（首页 `/`）。
 * 红线：工具本体首屏，零营销区块。H1 + 一行引言 + 行式卡片列表 + 页脚。
 * 文案逐字取 content-plan 页面 1。
 */
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ProblemCard from '../components/ProblemCard.vue'
import ErrorBar from '../components/ErrorBar.vue'
import EmptyState from '../components/EmptyState.vue'
import { useProblems } from '../composables/useProblems.js'
import { applyTdk, TDK_HOME, PROBLEM_RANGE_LABEL } from '../utils/tdk.js'

const router = useRouter()
const { items, loading, error, load } = useProblems()

onMounted(() => {
  applyTdk(TDK_HOME)
  load()
})

function gotoProblem(pid) {
  router.push(`/problems/${pid}`)
}
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
      <section class="list page__section" aria-label="题目列表">
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

        <ul v-else class="list__items">
          <li v-for="p in items" :key="p.id" class="list__item">
            <ProblemCard :problem="p" @click="gotoProblem(p.id)" />
          </li>
        </ul>
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
</style>
