<script setup>
/**
 * 代码编辑区：contenteditable <pre> + 语法高亮。
 * 单层结构——文字直接渲染在 pre 里，选中天然对齐（与题面代码块一致）。
 * 输入后防抖重新高亮（保存/恢复光标）；Tab 插入 4 空格；粘贴纯文本。
 */
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { highlightCode, langFromFilename } from '../utils/hljs.js'

const props = defineProps({
  modelValue: { type: String, default: '' },
  filename: { type: String, default: 'main.cpp' },
  readonly: { type: Boolean, default: false },
  minHeight: { type: String, default: '420px' }
})

const emit = defineEmits(['update:modelValue', 'upload'])

const area = ref(null)
let rehighlightTimer = null
let isComposing = false
let isInternalUpdate = false

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function getHighlightedHtml(text) {
  const lang = langFromFilename(props.filename)
  return highlightCode(text, lang) || escapeHtml(text)
}

/** 纯文本 → 光标偏移量 */
function getTextOffset(root, node, offset) {
  let textOffset = 0
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null)
  let current
  while ((current = walker.nextNode())) {
    if (current === node) return textOffset + offset
    textOffset += current.textContent.length
  }
  return textOffset
}

/** 光标偏移量 → Range（用于恢复光标） */
function setTextOffset(root, targetOffset) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null)
  let current
  let offset = 0
  while ((current = walker.nextNode())) {
    const len = current.textContent.length
    if (offset + len >= targetOffset) {
      const r = document.createRange()
      r.setStart(current, Math.min(targetOffset - offset, len))
      r.collapse(true)
      return r
    }
    offset += len
  }
  return null
}

/** 重新高亮并恢复光标 */
function rehighlight() {
  if (!area.value) return
  const selection = window.getSelection()
  let textOffset = 0
  let hasCursor = false

  if (selection && selection.rangeCount > 0) {
    const range = selection.getRangeAt(0)
    if (area.value.contains(range.startContainer)) {
      textOffset = getTextOffset(area.value, range.startContainer, range.startOffset)
      hasCursor = true
    }
  }

  const text = area.value.textContent || ''
  isInternalUpdate = true
  area.value.innerHTML = getHighlightedHtml(text)

  if (hasCursor) {
    const newRange = setTextOffset(area.value, textOffset)
    if (newRange) {
      selection.removeAllRanges()
      selection.addRange(newRange)
    }
  }
  isInternalUpdate = false
}

function onInput() {
  if (isComposing || isInternalUpdate) return
  const text = area.value.textContent || ''
  emit('update:modelValue', text)
  clearTimeout(rehighlightTimer)
  rehighlightTimer = setTimeout(rehighlight, 350)
}

function onKeydown(e) {
  if (e.key === 'Tab') {
    e.preventDefault()
    document.execCommand('insertText', false, '    ')
  }
}

function onPaste(e) {
  e.preventDefault()
  const text = (e.clipboardData || window.clipboardData).getData('text/plain')
  document.execCommand('insertText', false, text)
}

function onCompositionStart() { isComposing = true }
function onCompositionEnd() {
  isComposing = false
  onInput()
}

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

// 外部改 modelValue（如上传文件）→ 更新 DOM
watch(() => props.modelValue, (val) => {
  if (area.value && area.value.textContent !== val) {
    isInternalUpdate = true
    area.value.innerHTML = getHighlightedHtml(val)
    isInternalUpdate = false
  }
})

onMounted(() => {
  if (area.value) {
    area.value.innerHTML = getHighlightedHtml(props.modelValue)
    area.value.addEventListener('compositionstart', onCompositionStart)
    area.value.addEventListener('compositionend', onCompositionEnd)
  }
})

onBeforeUnmount(() => {
  clearTimeout(rehighlightTimer)
  if (area.value) {
    area.value.removeEventListener('compositionstart', onCompositionStart)
    area.value.removeEventListener('compositionend', onCompositionEnd)
  }
})
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
    <div
      ref="area"
      class="editor__code"
      :contenteditable="!readonly"
      :style="{ minHeight }"
      role="textbox"
      aria-multiline="true"
      aria-label="源码编辑区"
      spellcheck="false"
      @input="onInput"
      @keydown="onKeydown"
      @paste="onPaste"
    ></div>
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

.editor__code {
  display: block;
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
  color: var(--code-text);
  background: var(--code-bg);
  caret-color: var(--code-accent);
  outline: none;
  overflow: auto;
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
