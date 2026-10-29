<script setup>
/**
 * 深色代码块（design-spec 5.14）。
 * 样例块：顶部条 + 复制按钮；命令块：语言标 bash + 复制命令。
 * 复制成功瞬时切「已复制」1.2s。
 */
import { ref, computed } from 'vue'
import { highlightCode } from '../utils/hljs.js'

const props = defineProps({
  /** 顶部条左侧标签，如「样例输入」「bash」 */
  label: { type: String, default: '' },
  /** 复制按钮文案 */
  copyLabel: { type: String, default: '复制样例' },
  code: { type: String, default: '' },
  /** 禁用复制按钮 */
  noCopy: { type: Boolean, default: false },
  /** 围栏语言（bash/cpp/makefile…）；空=纯文本（样例 I/O 数据用） */
  language: { type: String, default: '' }
})

const copied = ref(false)
let timer = null

const displayCode = computed(() => (props.code == null ? '' : String(props.code)))
const highlighted = computed(() => (props.language ? highlightCode(displayCode.value, props.language) : ''))

async function copy() {
  try {
    await navigator.clipboard.writeText(displayCode.value)
    copied.value = true
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      copied.value = false
    }, 1200)
  } catch {
    copied.value = false
  }
}
</script>

<template>
  <figure class="code-block">
    <div class="code-block__bar">
      <figcaption class="code-block__label caption">{{ label }}</figcaption>
      <button
        v-if="!noCopy"
        type="button"
        class="code-block__copy"
        @click="copy"
      >{{ copied ? '已复制' : copyLabel }}</button>
    </div>
    <!-- eslint-disable-next-line vue/no-v-html —— highlightCode 输出可信 token span -->
    <pre class="code-block__body"><code v-if="highlighted" class="hljs" v-html="highlighted"></code><code v-else>{{ displayCode }}</code></pre>
  </figure>
</template>

<style scoped>
.code-block {
  margin: 0;
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--code-border);
}

.code-block__bar {
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-3);
  background: var(--code-bar-bg);
}

.code-block__label {
  color: var(--code-muted);
  margin: 0;
}

.code-block__copy {
  height: 24px;
  padding: 0 var(--space-2);
  border: 1px solid var(--code-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--code-text);
  font-size: var(--text-micro);
  font-weight: 500;
  cursor: pointer;
}

.code-block__copy:hover {
  background: var(--code-bar-bg);
}

.code-block__body {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  background: var(--code-bg);
  color: var(--code-text);
  font-family: var(--font-mono);
  font-size: var(--text-mono-code);
  line-height: var(--lh-mono-code);
  overflow-x: auto;
  white-space: pre;
}
</style>
