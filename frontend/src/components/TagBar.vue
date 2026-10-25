<script setup>
/**
 * 限制摘要标签栏（design-spec 5.13）。
 * 一行 6 枚：题号/模式/时限/内存/满分/构建。键名 muted，值 mono；模式值用主色底。
 */
import { computed } from 'vue'
import { modeShort } from '../utils/format.js'

const props = defineProps({
  problem: { type: Object, required: true }
})

const buildLabel = computed(() => {
  const b = props.problem.build || {}
  if (b.mode === 'make') return 'make inspector'
  // g++ 展示命令里的关键旗标，无命令时兜底
  const cmd = b.command || 'g++ -O2 -std=c++17'
  return cmd.replace(/\s*-o\s+\{bin\}\s*\{src\}/, '').trim() || 'g++'
})

const tags = computed(() => {
  const p = props.problem
  const limits = p.limits || {}
  return [
    { key: '题号', value: p.id, mono: true },
    { key: '模式', value: modeShort(p.contest_type), accent: true },
    { key: '时限', value: `${limits.time_ms != null ? limits.time_ms : 1000}ms`, mono: true },
    { key: '内存', value: `${limits.memory_mb != null ? limits.memory_mb : 256}MB`, mono: true },
    { key: '满分', value: String(p.score != null ? p.score : 100), mono: true },
    { key: '构建', value: buildLabel.value, mono: true }
  ]
})
</script>

<template>
  <ul class="tagbar" aria-label="题目限制摘要">
    <li
      v-for="t in tags"
      :key="t.key"
      class="tagbar__item"
      :class="{ 'tagbar__item--accent': t.accent }"
    >
      <span class="tagbar__key">{{ t.key }}</span>
      <span class="tagbar__val" :class="{ 'mono-data': t.mono }">{{ t.value }}</span>
    </li>
  </ul>
</template>

<style scoped>
.tagbar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  list-style: none;
  margin: 0;
  padding: 0;
}

.tagbar__item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 28px;
  padding: 0 10px;
  border-radius: var(--radius-sm);
  background: var(--bg-subtle);
  font-size: var(--text-caption);
  line-height: 1;
}

.tagbar__key {
  color: var(--text-muted);
  font-size: var(--text-caption);
}

.tagbar__val {
  color: var(--text-primary);
  font-size: var(--text-mono-badge);
  font-weight: 500;
}

.tagbar__item--accent {
  background: var(--primary-bg);
}

.tagbar__item--accent .tagbar__val {
  color: var(--primary);
  font-family: var(--font-mono);
}
</style>
