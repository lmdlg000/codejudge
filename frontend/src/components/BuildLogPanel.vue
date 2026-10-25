<script setup>
/**
 * CE 编译输出面板（design-spec 5.12 build_log 专用）。
 * 标题「编译器输出（末 200 行）」；首条含 error: 的行红条+加粗；
 * 默认展开（CE 时）；折叠按钮「展开/收起编译输出」。
 */
import { computed, ref } from 'vue'

const props = defineProps({
  buildLog: { type: String, default: '' },
  /** 构建超时（60s）判 CE 时为 true */
  buildTimeout: { type: Boolean, default: false }
})

const open = ref(true)
const uid = `buildlog-${Math.random().toString(36).slice(2, 9)}`

const lines = computed(() => String(props.buildLog || '').split(/\r?\n/))

/** 首条含 `error:` 的行号（高亮） */
const firstErrorIdx = computed(() => {
  return lines.value.findIndex((l) => /error:/i.test(l))
})

const hasErrorLine = computed(() => firstErrorIdx.value >= 0)
</script>

<template>
  <section class="blog" aria-label="编译器输出">
    <h4 class="blog__title">编译器输出（末 200 行）</h4>
    <p class="blog__caption caption">
      只显示末 200 行；完整输出已写入报告 JSON 的 build_log 字段。
    </p>
    <p v-if="buildTimeout" class="blog__hint caption">
      构建超过 60 秒被中止。检查模板递归或宏展开。
    </p>

    <button
      type="button"
      class="blog__toggle"
      :aria-expanded="open ? 'true' : 'false'"
      :aria-controls="uid"
      @click="open = !open"
    >
      <svg
        class="blog__chev"
        :class="{ 'blog__chev--open': open }"
        width="12"
        height="12"
        viewBox="0 0 12 12"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M2.5 4.5L6 8l3.5-3.5" />
      </svg>
      <span>{{ open ? '收起编译输出' : '展开编译输出' }}</span>
    </button>

    <div v-show="open" :id="uid" class="blog__body">
      <div
        v-for="(line, i) in lines"
        :key="i"
        class="blog__line"
        :class="{
          'blog__line--error': hasErrorLine && i === firstErrorIdx
        }"
      >{{ line }}</div>
    </div>
  </section>
</template>

<style scoped>
.blog {
  background: var(--bg-surface);
  border: var(--border);
  border-left: 3px solid var(--verdict-ce-text);
  border-radius: var(--radius);
  padding: var(--space-5) var(--space-6);
}

.blog__title {
  margin: 0;
  color: var(--verdict-ce-text);
}

.blog__caption {
  margin-top: var(--space-1);
  color: var(--text-secondary);
}

.blog__hint {
  margin-top: var(--space-2);
  color: var(--warning-text);
}

.blog__toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  height: var(--control-h-sm);
  margin-top: var(--space-2);
  padding: 0 var(--space-2);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  position: relative;
}

.blog__toggle::after {
  content: '';
  position: absolute;
  inset: 50% auto auto 50%;
  width: 100%;
  height: 44px;
  min-width: 44px;
  transform: translate(-50%, -50%);
}

.blog__toggle:hover {
  background: var(--primary-bg);
  color: var(--primary-hover);
}

.blog__chev {
  transition: transform var(--dur-fast) var(--ease-out);
}

.blog__chev--open {
  transform: rotate(180deg);
}

.blog__body {
  margin-top: var(--space-3);
  max-height: 480px;
  overflow: auto;
  background: var(--code-bg);
  border-radius: var(--radius);
  padding: var(--space-3) 0;
}

.blog__line {
  font-family: var(--font-mono);
  font-size: var(--text-mono-code);
  line-height: var(--lh-mono-code);
  color: var(--code-muted);
  padding: 0 var(--space-4);
  white-space: pre-wrap;
  word-break: break-all;
}

.blog__line--error {
  color: var(--code-error);
  font-weight: 700;
  border-left: 3px solid var(--code-error-bar);
  background: rgba(239, 68, 68, 0.12);
  padding-left: calc(var(--space-4) - 3px);
}
</style>
