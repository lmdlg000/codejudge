<script setup>
/**
 * 代码编辑区（design-spec 5.8）：textarea + 高亮遮罩层（overlay）。
 * textarea 自身无法语法高亮，用「透明字色 textarea + 背景 pre」叠加实现：
 * 两层字体/行高/内边距严格一致，滚动同步，光标仍走原生 textarea。
 * 预填 main 骨架；空码时父组件禁用提交；wrap="off" 横向滚动；
 * 焦点容器 2px 焦点环；label 关联（无障碍硬项）。
 */
import { computed, ref, onBeforeUnmount } from 'vue'
import { highlightCode, langFromFilename } from '../utils/hljs.js'

const props = defineProps({
  modelValue: { type: String, default: '' },
  filename: { type: String, default: 'main.cpp' },
  readonly: { type: Boolean, default: false },
  minHeight: { type: String, default: '420px' }
})

const emit = defineEmits(['update:modelValue', 'upload'])

const uid = `editor-${Math.random().toString(36).slice(2, 9)}`

const value = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

/** 高亮层 HTML（语言未知回退纯文本转义） */
const highlighted = computed(() => {
  const lang = langFromFilename(props.filename)
  return highlightCode(props.modelValue, lang) || escapeHtml(props.modelValue)
})

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

const area = ref(null)
const backdrop = ref(null)

/** textarea 滚动 → 高亮层同步 */
function onScroll() {
  if (!area.value || !backdrop.value) return
  backdrop.value.scrollTop = area.value.scrollTop
  backdrop.value.scrollLeft = area.value.scrollLeft
}

let resizeObs = null
function onBackdropRef(el) {
  backdrop.value = el
  if (el && typeof ResizeObserver !== 'undefined' && area.value) {
    resizeObs = new ResizeObserver(() => onScroll())
    resizeObs.observe(area.value)
  }
}

onBeforeUnmount(() => {
  if (resizeObs) resizeObs.disconnect()
})

function onFile(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    emit('upload', String(reader.result || ''))
    e.target.value = ''
  }
  reader.readAsText(file)
}
</script>

<template>
  <div class="editor" :style="{ '--editor-min': minHeight }">
    <div class="editor__bar">
      <span class="editor__filename mono-data">{{ filename }}</span>
      <label class="editor__upload">
        上传 .cpp 文件
        <input
          class="sr-only"
          type="file"
          accept=".cpp,.cc,.cxx,.h,.hpp,text/plain"
          @change="onFile"
        />
      </label>
    </div>
    <label class="sr-only" :for="uid">源码编辑区</label>
    <div class="editor__box">
      <!-- 高亮遮罩层：与 textarea 逐像素对齐 -->
      <pre
        :ref="onBackdropRef"
        class="editor__hl"
        aria-hidden="true"
      ><code class="hljs" v-html="highlighted"></code></pre>
      <textarea
        :id="uid"
        ref="area"
        v-model="value"
        class="editor__area"
        :readonly="readonly"
        spellcheck="false"
        wrap="off"
        placeholder="把 main.cpp 的内容贴到这里"
        @scroll="onScroll"
      ></textarea>
    </div>
  </div>
</template>

<style scoped>
.editor {
  background: var(--code-bg);
  border: 1px solid var(--code-border);
  border-radius: var(--radius);
  overflow: hidden;
}

.editor:focus-within {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

.editor__bar {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-3);
  background: var(--code-bar-bg);
}

.editor__filename {
  color: var(--code-muted);
  font-weight: 500;
}

.editor__upload {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 var(--space-2);
  border: 1px solid var(--code-border);
  border-radius: var(--radius-sm);
  color: var(--code-text);
  font-size: var(--text-micro);
  font-weight: 500;
  cursor: pointer;
}

.editor__upload:hover {
  background: var(--code-bar-bg);
}

.editor__upload:focus-within {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

/* overlay 容器：两层同尺寸叠放 */
.editor__box {
  position: relative;
  min-height: var(--editor-min);
}

.editor__hl,
.editor__area {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-mono);
  font-size: var(--text-mono-code);
  line-height: var(--lh-mono-code);
  letter-spacing: normal;
  tab-size: 4;
  white-space: pre;
  word-break: normal;
  overflow-wrap: normal;
  font-variant-ligatures: none;
  font-feature-settings: "liga" 0, "calt" 0;
  border: none;
  border-radius: 0;
}

.editor__hl {
  position: absolute;
  inset: 0;
  overflow: auto;
  background: var(--code-bg);
  color: var(--code-text);
  pointer-events: none;
  user-select: none;
}

.editor__hl code {
  font: inherit;
  white-space: inherit;
  background: transparent;
  display: block;
  min-height: 100%;
}

.editor__area {
  position: relative;
  display: block;
  width: 100%;
  min-height: var(--editor-min);
  resize: vertical;
  background: transparent;
  color: transparent;
  caret-color: var(--code-accent);
  outline: none;
  overflow: auto;
}

.editor__area::placeholder {
  color: var(--code-muted);
}

.editor__area::selection {
  background: var(--focus-ring);
  color: transparent;
}

@media (max-width: 1279px) {
  .editor {
    --editor-min: 360px;
  }
}

@media (max-width: 1023px) {
  .editor {
    --editor-min: 320px;
  }
}

@media (max-width: 640px) {
  .editor {
    --editor-min: 280px;
  }
}
</style>
