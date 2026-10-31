<script setup>
/**
 * 提交源码回显（design-spec 5.12 源码回显）。
 * 默认折叠；按钮「展开源码 / 收起源码」；每文件一节：文件名 + 等宽代码块 + 复制。
 * 按文件名推断语言做语法高亮（cpp/makefile/bash…）；未知扩展回退纯文本。
 */
import { ref, computed } from 'vue'
import { highlightCode, langFromFilename } from '../utils/hljs.js'

const props = defineProps({
  files: { type: Array, default: () => [] }
})

const open = ref(false)
const uid = `src-echo-${Math.random().toString(36).slice(2, 9)}`
const copiedName = ref('')

const count = computed(() => (props.files || []).length)

/** 每文件：推断语言 → token HTML（'' = 纯文本回退） */
const rendered = computed(() =>
  (props.files || []).map((f) => {
    const content = f && f.content != null ? String(f.content) : ''
    const lang = langFromFilename(f && f.name)
    return {
      name: (f && f.name) || '',
      content,
      html: lang ? highlightCode(content, lang) : ''
    }
  })
)

async function copyFile(f) {
  try {
    await navigator.clipboard.writeText(f.content || '')
    copiedName.value = f.name
    setTimeout(() => {
      if (copiedName.value === f.name) copiedName.value = ''
    }, 1200)
  } catch {
    copiedName.value = ''
  }
}
</script>

<template>
  <section v-if="count" class="src" aria-label="提交源码">
    <h3 class="src__title">本次提交源码（{{ count }} 个文件）</h3>
    <button
      type="button"
      class="src__toggle"
      :aria-expanded="open ? 'true' : 'false'"
      :aria-controls="uid"
      @click="open = !open"
    >
      <svg
        class="src__chev"
        :class="{ 'src__chev--open': open }"
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
      <span>{{ open ? '收起源码' : '展开源码' }}</span>
    </button>

    <div v-show="open" :id="uid" class="src__body">
      <div v-for="f in rendered" :key="f.name" class="src__file">
        <div class="src__file-bar">
          <span class="mono-data src__filename">{{ f.name }}</span>
          <button type="button" class="src__copy" @click="copyFile(f)">
            {{ copiedName === f.name ? '已复制' : '复制' }}
          </button>
        </div>
        <!-- eslint-disable-next-line vue/no-v-html —— highlightCode 输出可信 token span -->
        <pre class="src__code"><code v-if="f.html" class="hljs" v-html="f.html"></code><code v-else>{{ f.content }}</code></pre>
      </div>
    </div>
  </section>
</template>

<style scoped>
.src {
  background: var(--bg-surface);
  border: var(--border);
  border-radius: var(--radius);
  padding: var(--space-5) var(--space-6);
}

.src__title {
  margin: 0;
}

.src__toggle {
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

.src__toggle::after {
  content: '';
  position: absolute;
  inset: 50% auto auto 50%;
  width: 100%;
  height: 44px;
  min-width: 44px;
  transform: translate(-50%, -50%);
}

.src__toggle:hover {
  background: var(--primary-bg);
  color: var(--primary-hover);
}

.src__chev {
  transition: transform var(--dur-fast) var(--ease-out);
}

.src__chev--open {
  transform: rotate(180deg);
}

.src__body {
  margin-top: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.src__file {
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--code-border);
}

.src__file-bar {
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-3);
  background: var(--code-bar-bg);
}

.src__filename {
  color: var(--code-muted);
  font-weight: 500;
}

.src__copy {
  height: 24px;
  padding: 0 var(--space-2);
  border: 1px solid #334155;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--code-text);
  font-size: var(--text-micro);
  font-weight: 500;
  cursor: pointer;
}

.src__copy:hover {
  background: #334155;
}

.src__code {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  background: var(--code-bg);
  color: var(--code-text);
  font-family: var(--font-mono);
  font-size: var(--text-mono-code);
  line-height: var(--lh-mono-code);
  max-height: 320px;
  overflow: auto;
  white-space: pre;
  font-variant-ligatures: none;
  font-feature-settings: "liga" 0, "calt" 0;
}
</style>
