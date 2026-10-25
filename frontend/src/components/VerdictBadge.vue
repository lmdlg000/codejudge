<script setup>
/**
 * 判定徽章（design-spec 5.4 / 2.3）。
 * 10% 色调底 + 800 档深色文字 + 300 档细边框 + 左 3px 同色系深条。
 * 文字主信道：徽章内固定显示判定代码；aria-label 给中文全称（色弱可用）。
 */
import { computed } from 'vue'
import { verdictMeta } from '../utils/verdicts.js'

const props = defineProps({
  verdict: { type: String, required: true },
  large: { type: Boolean, default: false }
})

const meta = computed(() => verdictMeta(props.verdict))
const cls = computed(() => `badge--${String(props.verdict || 'SE').toLowerCase()}`)
</script>

<template>
  <span
    class="badge"
    :class="[cls, { 'badge--lg': large }]"
    :title="meta.label"
    :aria-label="`判定：${meta.label}`"
  >{{ meta.code }}</span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: var(--badge-h);
  min-width: 48px;
  padding: 0 var(--space-2);
  border-radius: var(--radius-sm);
  border: 1px solid;
  border-left: 3px solid;
  font-family: var(--font-mono);
  font-size: var(--text-mono-badge);
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.badge--lg {
  height: var(--badge-h-lg);
  min-width: 64px;
  font-size: 14px;
}

/* —— 7 色判定（tokens.css verdict-* 三件套）—— */
.badge--ac {
  color: var(--verdict-ac-text);
  background: var(--verdict-ac-bg);
  border-color: var(--verdict-ac-border);
  border-left-color: var(--verdict-ac-text);
}
.badge--pe {
  color: var(--verdict-pe-text);
  background: var(--verdict-pe-bg);
  border-color: var(--verdict-pe-border);
  border-left-color: var(--verdict-pe-text);
}
.badge--wa {
  color: var(--verdict-wa-text);
  background: var(--verdict-wa-bg);
  border-color: var(--verdict-wa-border);
  border-left-color: var(--verdict-wa-text);
}
.badge--tle {
  color: var(--verdict-tle-text);
  background: var(--verdict-tle-bg);
  border-color: var(--verdict-tle-border);
  border-left-color: var(--verdict-tle-text);
}
.badge--re {
  color: var(--verdict-re-text);
  background: var(--verdict-re-bg);
  border-color: var(--verdict-re-border);
  border-left-color: var(--verdict-re-text);
}
.badge--ce {
  color: var(--verdict-ce-text);
  background: var(--verdict-ce-bg);
  border-color: var(--verdict-ce-border);
  border-left-color: var(--verdict-ce-text);
}
.badge--se {
  color: var(--verdict-se-text);
  background: var(--verdict-se-bg);
  border-color: var(--verdict-se-border);
  border-left-color: var(--verdict-se-text);
}
</style>
