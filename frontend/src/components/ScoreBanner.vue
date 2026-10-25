<script setup>
/**
 * 得分横幅（design-spec 5.5，格式逐字冻结）。
 * 主行：通过 {passed}/{total} · 通过率 {rate}% · 得分 {score}/{max_score}
 * 防破版：拆 .seg/.sep 逐段 nowrap + tabular-nums，容器 overflow-x:auto。
 */
import { computed } from 'vue'
import VerdictBadge from './VerdictBadge.vue'
import { bannerSegments, bannerNote, formatNum } from '../utils/format.js'

const props = defineProps({
  summary: { type: Object, required: true },
  verdict: { type: String, required: true },
  mode: { type: String, required: true }, // acm | oi
  submissionId: { type: String, default: '' }
})

const segs = computed(() => bannerSegments(props.summary))
const note = computed(() => bannerNote(props.mode, props.summary))
const accentClass = computed(() => `score-banner--${String(props.verdict || 'se').toLowerCase()}`)
</script>

<template>
  <section
    class="score-banner"
    :class="accentClass"
    aria-label="得分横幅"
  >
    <div class="score-banner__row">
      <div class="score-banner__main">
        <!-- 句式冻结：三段 seg 由 sep 分隔，各段 nowrap -->
        <span class="seg">{{ segs.passed }}</span>
        <span class="sep" aria-hidden="true">·</span>
        <span class="seg">{{ segs.rate }}</span>
        <span class="sep" aria-hidden="true">·</span>
        <span class="seg">{{ segs.score }}</span>
      </div>
      <div class="score-banner__side">
        <VerdictBadge :verdict="verdict" large />
        <span v-if="submissionId" class="score-banner__sid mono-data">{{ submissionId }}</span>
      </div>
    </div>
    <p class="score-banner__note">{{ note }}</p>
  </section>
</template>

<style scoped>
.score-banner {
  background: var(--bg-surface);
  border: var(--border);
  border-left: 4px solid var(--text-muted);
  border-radius: var(--radius);
  padding: var(--space-5) var(--space-6);
}

.score-banner__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

/* 防换行破版：主行整行 nowrap，溢出走横向滚动 */
.score-banner__main {
  display: flex;
  align-items: baseline;
  flex-wrap: nowrap;
  white-space: nowrap;
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: var(--text-banner);
  font-weight: 700;
  line-height: 1.3;
  color: var(--text-primary);
  max-width: 100%;
}

.score-banner__main .seg {
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.score-banner__main .sep {
  margin: 0 10px;
  color: var(--text-muted);
  flex: none;
}

.score-banner__side {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.score-banner__sid {
  color: var(--text-muted);
  font-weight: 500;
}

.score-banner__note {
  margin-top: var(--space-2);
  font-size: var(--text-caption);
  line-height: var(--lh-caption);
  color: var(--text-secondary);
}

/* 左条 = 总判定色 */
.score-banner--ac { border-left-color: var(--verdict-ac-text); }
.score-banner--pe { border-left-color: var(--verdict-pe-text); }
.score-banner--wa { border-left-color: var(--verdict-wa-text); }
.score-banner--tle { border-left-color: var(--verdict-tle-text); }
.score-banner--re { border-left-color: var(--verdict-re-text); }
.score-banner--ce { border-left-color: var(--verdict-ce-text); }
.score-banner--se { border-left-color: var(--verdict-se-text); }
</style>
