<script setup>
/**
 * 代码编辑区（design-spec 5.8）：textarea + 高亮遮罩层（overlay）。
 * textarea 自身无法语法高亮，用「透明字色 textarea + 背景 pre」叠加实现：
 * 两层字体/行高/内边距严格一致，滚动同步，光标仍走原生 textarea。
 * 预填 main 骨架；空码时父组件禁用提交；wrap="off" 横向滚动；
 * 焦点容器 2px 焦点环；label 关联（无障碍硬项）。
 */
import { computed, ref, onBeforeUnmount, nextTick, watch } from 'vue'
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

/**
 * 运行时像素级对齐：用 Range API 测量 pre 中首行文本的实际位置，
 * 与 textarea 的内容起点对比，动态补偿偏移。
 * 这不依赖 CSS 猜测，直接测量浏览器实际渲染结果。
 */
function alignOverlay() {
  if (!area.value || !backdrop.value) return
  const code = backdrop.value.querySelector('code')
  if (!code || !code.firstChild) return

  // 用 Range 测量 pre/code 中首行文本的首字符位置
  const range = document.createRange()
  const firstNode = code.firstChild
  if (firstNode.nodeType !== Node.TEXT_NODE && firstNode.firstChild) {
    range.setStart(firstNode.firstChild, 0)
  } else {
    range.setStart(firstNode, 0)
  }
  range.setEnd(range.startContainer, 1)
  const textRect = range.getBoundingClientRect()
  range.detach()

  // textarea 的内容起点 = padding-top + border-top
  const aStyle = window.getComputedStyle(area.value)
  const aPadTop = parseFloat(aStyle.paddingTop) || 0
  const aBorderTop = parseFloat(aStyle.borderTopWidth) || 0
  const areaRect = area.value.getBoundingClientRect()
  const expectedY = areaRect.top + aBorderTop + aPadTop

  // pre 的内容起点
  const pStyle = window.getComputedStyle(backdrop.value)
  const pPadTop = parseFloat(pStyle.paddingTop) || 0
  const pBorderTop = parseFloat(pStyle.borderTopWidth) || 0
  const preRect = backdrop.value.getBoundingClientRect()
  const actualY = preRect.top + pBorderTop + pPadTop

  // 补偿垂直偏移（textarea 文本首行 vs pre 文本首行）
  const deltaY = expectedY - actualY

  // 补偿水平偏移（首个字符的 X 位置）
  const expectedX = areaRect.left + (parseFloat(aStyle.paddingLeft) || 0) + (parseFloat(aStyle.borderLeftWidth) || 0)
  const deltaX = expectedX - textRect.left

  if (Math.abs(deltaY) > 0.5 || Math.abs(deltaX) > 0.5) {
    backdrop.value.style.transform = `translate(${deltaX}px, ${deltaY}px)`
  } else {
    backdrop.value.style.transform = ''
  }
}

let resizeObs = null
function onBackdropRef(el) {
  backdrop.value = el
  if (el && typeof ResizeObserver !== 'undefined' && area.value) {
    resizeObs = new ResizeObserver(() => {
      onScroll()
      alignOverlay()
    })
    resizeObs.observe(area.value)
    // 首帧对齐
    requestAnimationFrame(() => alignOverlay())
  }
}

onBeforeUnmount(() => {
  if (resizeObs) resizeObs.disconnect()
})

// 内容变化后重新对齐（v-html 更新后 DOM 需要一帧渲染）
watch(highlighted, () => {
  nextTick(() => {
    requestAnimationFrame(() => alignOverlay())
  })
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
  box-sizing: border-box;
  font-family: var(--font-mono);
  font-size: var(--text-mono-code);
  /* 用固定像素行高避免小数行高在 textarea/pre 间取整差异导致错位 */
  line-height: 22px;
  letter-spacing: normal;
  tab-size: 4;
  white-space: pre;
  word-break: normal;
  overflow-wrap: normal;
  font-variant-ligatures: none;
  font-feature-settings: "liga" 0, "calt" 0;
  font-synthesis: none;
  text-rendering: geometricPrecision;
  border: none;
  border-radius: 0;
  scrollbar-gutter: stable;
}

.editor__hl {
  position: absolute;
  inset: 0;
  overflow: scroll;
  background: var(--code-bg);
  color: var(--code-text);
  pointer-events: none;
  user-select: none;
  /* 滚动条不可见但占位——保证与 textarea 内容区等宽 */
  scrollbar-color: transparent transparent;
}

.editor__hl::-webkit-scrollbar {
  background: transparent;
}
.editor__hl::-webkit-scrollbar-thumb {
  background: transparent;
}
.editor__hl::-webkit-scrollbar-track {
  background: transparent;
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
  overflow: scroll;
}

.editor__area::placeholder {
  color: var(--code-muted);
}

.editor__area::selection {
  background: var(--focus-ring);
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
