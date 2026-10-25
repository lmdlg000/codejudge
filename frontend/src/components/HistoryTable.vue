<script setup>
/**
 * 提交历史表（design-spec 5.3，微裁定已定）。
 * 列冻结：时间 | 题目 | 提交文件 | 判定 | 通过 | 得分 | 操作。
 * file_label 整列缺失边界：列头常驻不整列隐藏，缺失单元格统一显示「—」（表头对齐不跳变）。
 * 操作列：「看结果」「看 JSON」；整行可点（= 看结果）+ tabindex + focus-ring。
 * <640 转堆叠卡片。
 */
import VerdictBadge from './VerdictBadge.vue'
import { formatDateTime, formatNum, modeShort } from '../utils/format.js'
import { ASYNC_STATUS_LABEL, isHumanReviewed } from '../api/asyncSubmit.js'

const props = defineProps({
  items: { type: Array, default: () => [] },
  /** 行来源徽章（Δ2-4）：cloud=「云端 · 按账号隔离」info 色；local=「本机」SE 灰 */
  source: { type: String, default: '' }
})

const emit = defineEmits(['open', 'json'])

/** ΔAI：异步流行显示状态标签（human_reviewed_* 变体各自标签） */
function asyncLabel(status) {
  return ASYNC_STATUS_LABEL[status] || (isHumanReviewed(status) ? '复核完成' : '评分中')
}

/** chip 样式类：human_reviewed_* 共用 human_reviewed 色 */
function asyncChipClass(status) {
  const s = isHumanReviewed(status) ? 'human_reviewed' : status || 'judging'
  return `async-chip--${s}`
}

function openRow(sid) {
  emit('open', sid)
}

function openJson(sid) {
  emit('json', sid)
}

function onRowKey(e, sid) {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    openRow(sid)
  }
}

/** file_label 微裁定：缺失显示「—」，不整列隐藏 */
function fileLabelOf(it) {
  return it && it.file_label ? it.file_label : '—'
}
</script>

<template>
  <!-- ====== ≥640：表格 ====== -->
  <div class="htable-wrap">
    <table class="htable">
      <caption class="sr-only">提交历史列表</caption>
      <thead>
        <tr>
          <th scope="col">时间</th>
          <th scope="col">题目</th>
          <th scope="col">提交文件</th>
          <th scope="col">判定</th>
          <th scope="col">通过</th>
          <th scope="col">得分</th>
          <th scope="col">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="it in items"
          :key="it.submission_id"
          class="htable__row"
          tabindex="0"
          role="link"
          :aria-label="`查看 ${it.problem_id} 的判定结果`"
          @click="openRow(it.submission_id)"
          @keydown="onRowKey($event, it.submission_id)"
        >
          <td class="htable__time mono-data">{{ formatDateTime(it.created_at) }}</td>
          <td class="htable__problem">
            <span class="mono-data">{{ it.problem_id }}</span>
            <span class="htable__ptitle">{{ it.problem_title }}</span>
            <span class="htable__mode">{{ modeShort(it.mode) }}</span>
            <span
              v-if="source"
              class="htable__src"
              :class="`htable__src--${source}`"
            >{{ source === 'cloud' ? '云端 · 按账号隔离' : '本机' }}</span>
          </td>
          <!-- 列头常驻，缺失显示「—」 -->
          <td class="htable__file mono-data">{{ fileLabelOf(it) }}</td>
          <td>
            <VerdictBadge v-if="it.verdict" :verdict="it.verdict" />
          <span v-else class="async-chip mono-data" :class="asyncChipClass(it.async_status)">{{ asyncLabel(it.async_status) }}</span>
          </td>
          <td class="htable__num mono-data">
            {{ formatNum(it.summary && it.summary.passed) }}/{{ formatNum(it.summary && it.summary.total) }}
          </td>
          <td class="htable__num mono-data">
            {{ formatNum(it.summary && it.summary.score) }}/{{ formatNum(it.summary && it.summary.max_score) }}
          </td>
          <td class="htable__ops">
            <button
              type="button"
              class="htable__op"
              @click.stop="openRow(it.submission_id)"
            >看结果</button>
            <button
              type="button"
              class="htable__op"
              @click.stop="openJson(it.submission_id)"
            >看 JSON</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- ====== <640：堆叠卡片 ====== -->
  <ul class="hcards" aria-label="提交历史列表">
    <li
      v-for="it in items"
      :key="it.submission_id"
      class="hcard"
      tabindex="0"
      role="link"
      :aria-label="`查看 ${it.problem_id} 的判定结果`"
      @click="openRow(it.submission_id)"
      @keydown="onRowKey($event, it.submission_id)"
    >
      <div class="hcard__top">
        <VerdictBadge v-if="it.verdict" :verdict="it.verdict" />
        <span v-else class="async-chip mono-data" :class="asyncChipClass(it.async_status)">{{ asyncLabel(it.async_status) }}</span>
        <span class="hcard__time mono-data">{{ formatDateTime(it.created_at) }}</span>
      </div>
      <p class="hcard__problem">
        <span class="mono-data">{{ it.problem_id }}</span> {{ it.problem_title }}
        <span
          v-if="source"
          class="htable__src"
          :class="`htable__src--${source}`"
        >{{ source === 'cloud' ? '云端 · 按账号隔离' : '本机' }}</span>
      </p>
      <p class="hcard__file mono-data">{{ fileLabelOf(it) }} · {{ modeShort(it.mode) }}</p>
      <p class="hcard__score mono-data">
        通过 {{ formatNum(it.summary && it.summary.passed) }}/{{ formatNum(it.summary && it.summary.total) }}
        · 得分 {{ formatNum(it.summary && it.summary.score) }}/{{ formatNum(it.summary && it.summary.max_score) }}
      </p>
    </li>
  </ul>
</template>

<style scoped>
.htable-wrap {
  background: var(--bg-surface);
  border: var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.htable {
  width: 100%;
  border-collapse: collapse;
}

.htable th {
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

.htable td {
  height: var(--table-row-h);
  padding: var(--space-2) var(--space-3);
  border-bottom: var(--border);
  font-size: var(--text-body);
  vertical-align: middle;
}

.htable tbody tr:last-child td {
  border-bottom: none;
}

.htable__row {
  cursor: pointer;
}

.htable__row:hover {
  background: var(--primary-bg);
}

.htable__row:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: -2px;
}

.htable__time {
  color: var(--text-secondary);
  white-space: nowrap;
}

.htable__problem {
  min-width: 0;
}

.htable__ptitle {
  margin-left: var(--space-2);
}

.htable__mode {
  display: inline-flex;
  align-items: center;
  height: 20px;
  margin-left: var(--space-2);
  padding: 0 var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--primary-bg);
  color: var(--primary);
  font-family: var(--font-mono);
  font-size: var(--text-mono-badge);
  font-weight: 700;
}

/* 行来源徽章（Δ2-4）：22px，云端 info 三件套 / 本机 SE 灰三件套 */
.htable__src {
  display: inline-flex;
  align-items: center;
  height: 22px;
  margin-left: var(--space-2);
  padding: 0 var(--space-2);
  border: 1px solid;
  border-left: 3px solid;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--text-mono-badge);
  font-weight: 700;
  white-space: nowrap;
}

.htable__src--cloud {
  color: var(--info-text);
  background: var(--info-bg);
  border-color: var(--info-border);
  border-left-color: var(--info-text);
}

.htable__src--local {
  color: var(--verdict-se-text);
  background: var(--verdict-se-bg);
  border-color: var(--verdict-se-border);
  border-left-color: var(--verdict-se-text);
}

/* 提交文件列：列宽 140px，缺失显示「—」 */
.htable__file {
  width: 140px;
  max-width: 140px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.htable__num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.htable__ops {
  white-space: nowrap;
}

.htable__op {
  height: var(--control-h-sm);
  padding: 0 var(--space-2);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--primary);
  font-size: var(--text-caption);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}

.htable__op + .htable__op {
  margin-left: var(--space-1);
}

.htable__op:hover {
  background: var(--primary-bg);
  color: var(--primary-hover);
}

/* —— 堆叠卡片（<640） —— */
.hcards {
  display: none;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: var(--space-3);
}

.hcard {
  background: var(--bg-surface);
  border: var(--border);
  border-radius: var(--radius);
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
}

.hcard:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

.hcard__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.hcard__time {
  color: var(--text-secondary);
}

.hcard__problem {
  margin-top: var(--space-2);
  font-size: var(--text-body);
}

.hcard__file {
  margin-top: var(--space-1);
  color: var(--text-secondary);
}

.hcard__score {
  margin-top: var(--space-1);
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1023px) {
  .htable-wrap {
    overflow-x: auto;
  }

  .htable {
    min-width: 760px;
  }
}

@media (max-width: 639px) {
  .htable-wrap {
    display: none;
  }

  .hcards {
    display: flex;
    flex-direction: column;
  }
}

/* ΔAI 异步流状态标签（判定列降级显示） */
.async-chip {
  display: inline-flex;
  align-items: center;
  height: var(--badge-h);
  padding: 0 8px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  font-size: var(--text-mono-badge);
  white-space: nowrap;
}
.async-chip--judging {
  color: var(--info-text);
  background: var(--info-bg);
  border-color: var(--info-border);
}
.async-chip--ai_scored {
  color: var(--success-text);
  background: var(--success-bg);
  border-color: var(--success-border);
}
.async-chip--pending_review {
  color: var(--warning-text);
  background: var(--warning-bg);
  border-color: var(--warning-border);
}
.async-chip--human_reviewed {
  color: var(--primary);
  background: var(--primary-bg);
  border-color: var(--primary);
}
</style>
