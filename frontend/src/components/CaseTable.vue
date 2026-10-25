<script setup>
/**
 * 逐用例判定表格（design-spec 5.3，列冻结：用例 | 判定 | 耗时 | 权重 | 提示）。
 * 响应式降级顺序（写死）：≥1024 全列 → 640–1023 横向滚动保全列 → <640 堆叠卡片。
 * stderr_tail 折叠：看 stderr / 收起 stderr。
 * 输出对比：契约 CaseResult 无 expected/actual 字段，不渲染入口（content-plan 注明「若引擎提供」）。
 */
import { ref, computed } from 'vue'
import VerdictBadge from './VerdictBadge.vue'
import { formatNum, EM_DASH } from '../utils/format.js'
import { verdictMeta, reExplain } from '../utils/verdicts.js'

const props = defineProps({
  cases: { type: Array, default: () => [] }
})

const openStderr = ref({})

function toggleStderr(name) {
  openStderr.value = { ...openStderr.value, [name]: !openStderr.value[name] }
}

function msgOf(c) {
  return c.message && String(c.message).trim() ? c.message : EM_DASH
}

function timeOf(c) {
  return `${formatNum(c.time_ms)}ms`
}

function isTleLimit(c) {
  return c.verdict === 'TLE'
}

const rows = computed(() =>
  (props.cases || []).map((c) => ({
    ...c,
    meta: verdictMeta(c.verdict),
    hasStderr: !!(c.stderr_tail && String(c.stderr_tail).trim()),
    reText: c.verdict === 'RE' ? reExplain(c) : ''
  }))
)
</script>

<template>
  <!-- ====== ≥640：表格（640–1023 横向滚动保全列） ====== -->
  <div class="case-table-wrap">
    <table class="case-table">
      <caption class="sr-only">逐用例判定结果</caption>
      <thead>
        <tr>
          <th scope="col">用例</th>
          <th scope="col">判定</th>
          <th scope="col">耗时</th>
          <th scope="col">权重</th>
          <th scope="col">提示</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="row in rows" :key="row.name">
          <tr>
            <td class="case-table__name mono-data">{{ row.name }}</td>
            <td>
              <VerdictBadge :verdict="row.verdict" />
              <span class="sr-only">{{ row.meta.label }}</span>
            </td>
            <td
              class="case-table__num mono-data"
              :class="{ 'case-table__num--warn': isTleLimit(row) }"
            >{{ timeOf(row) }}</td>
            <td class="case-table__num mono-data">{{ formatNum(row.weight) }}</td>
            <td class="case-table__msg">
              <span class="case-table__msg-text" :title="row.message || ''">{{ msgOf(row) }}</span>
              <button
                v-if="row.hasStderr"
                type="button"
                class="case-table__toggle"
                :aria-expanded="openStderr[row.name] ? 'true' : 'false'"
                :aria-controls="`stderr-${row.name}`"
                @click="toggleStderr(row.name)"
              >{{ openStderr[row.name] ? '收起 stderr' : '看 stderr' }}</button>
            </td>
          </tr>
          <!-- stderr 展开行 -->
          <tr v-if="row.hasStderr && openStderr[row.name]">
            <td colspan="5" class="case-table__detail">
              <div :id="`stderr-${row.name}`">
                <p v-if="row.reText" class="case-table__re">{{ row.reText }}</p>
                <pre class="case-table__stderr">{{ row.stderr_tail }}</pre>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>

  <!-- ====== <640：堆叠卡片（列表语义，不保留 table 壳） ====== -->
  <ul class="case-cards" aria-label="逐用例判定结果">
    <li v-for="row in rows" :key="row.name" class="case-card">
      <div class="case-card__head">
        <VerdictBadge :verdict="row.verdict" />
        <span class="case-card__name mono-data">{{ row.name }}</span>
        <span class="sr-only">{{ row.meta.label }}</span>
      </div>
      <div class="case-card__facts mono-data">
        <span :class="{ 'case-table__num--warn': isTleLimit(row) }">{{ timeOf(row) }}</span>
        <span aria-hidden="true">·</span>
        <span>权重 {{ formatNum(row.weight) }}</span>
      </div>
      <p class="case-card__msg">{{ msgOf(row) }}</p>
      <template v-if="row.hasStderr">
        <button
          type="button"
          class="case-table__toggle"
          :aria-expanded="openStderr[row.name] ? 'true' : 'false'"
          :aria-controls="`stderr-m-${row.name}`"
          @click="toggleStderr(row.name)"
        >{{ openStderr[row.name] ? '收起 stderr' : '看 stderr' }}</button>
        <div v-if="openStderr[row.name]" :id="`stderr-m-${row.name}`">
          <p v-if="row.reText" class="case-table__re">{{ row.reText }}</p>
          <pre class="case-table__stderr">{{ row.stderr_tail }}</pre>
        </div>
      </template>
    </li>
  </ul>
</template>

<style scoped>
/* —— 表格（≥640） —— */
.case-table-wrap {
  background: var(--bg-surface);
  border: var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.case-table {
  width: 100%;
  border-collapse: collapse;
}

.case-table th {
  height: var(--table-head-h);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-subtle);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-align: left;
  border-bottom: var(--border);
}

.case-table td {
  height: var(--table-row-compact-h);
  padding: var(--space-2) var(--space-3);
  border-bottom: var(--border);
  font-size: var(--text-body);
  vertical-align: middle;
}

.case-table tbody tr:last-child td {
  border-bottom: none;
}

.case-table__name {
  color: var(--text-primary);
  font-weight: 500;
  white-space: nowrap;
}

.case-table__num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
  white-space: nowrap;
}

.case-table__num--warn {
  color: var(--warning-text);
}

.case-table__msg {
  color: var(--text-secondary);
  font-size: var(--text-caption);
  max-width: 0;
  width: 45%;
}

.case-table__msg-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.case-table__toggle {
  display: inline-flex;
  align-items: center;
  height: var(--control-h-sm);
  margin-left: var(--space-2);
  padding: 0 var(--space-2);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--primary);
  font-size: var(--text-caption);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  vertical-align: middle;
}

.case-table__toggle:hover {
  color: var(--primary-hover);
  background: var(--primary-bg);
}

.case-table__detail {
  background: var(--bg-subtle);
  padding: var(--space-3) !important;
  height: auto !important;
}

.case-table__re {
  margin-bottom: var(--space-2);
  font-size: var(--text-caption);
  color: var(--text-primary);
}

.case-table__stderr {
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

/* —— 堆叠卡片（<640） —— */
.case-cards {
  display: none;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: var(--space-3);
}

.case-card {
  background: var(--bg-surface);
  border: var(--border);
  border-radius: var(--radius);
  padding: var(--space-3) var(--space-4);
}

.case-card__head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.case-card__name {
  color: var(--text-primary);
  font-weight: 500;
}

.case-card__facts {
  margin-top: var(--space-2);
  display: flex;
  gap: var(--space-2);
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.case-card__msg {
  margin-top: var(--space-2);
  font-size: var(--text-caption);
  line-height: var(--lh-caption);
  color: var(--text-secondary);
  word-break: break-word;
}

.case-card .case-table__stderr {
  margin-top: var(--space-2);
}

/* —— 断点 640–1023：表格横向滚动保全列 —— */
@media (max-width: 1023px) {
  .case-table-wrap {
    overflow-x: auto;
  }

  .case-table {
    min-width: 640px;
  }
}

/* —— <640：表格转堆叠卡片 —— */
@media (max-width: 639px) {
  .case-table-wrap {
    display: none;
  }

  .case-cards {
    display: flex;
    flex-direction: column;
  }
}
</style>
