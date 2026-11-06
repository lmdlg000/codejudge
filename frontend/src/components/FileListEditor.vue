<script setup>
/**
 * 多文件提交面板 —— 「多个源代码上传提交评测」核心 UI。
 * 能力：多选上传 / 新建空文件 / 选中编辑 / 删除；文件名白名单与后端一致
 * （字母数字 _ . -，1–64 字符）；内容以文本读入（源码提交）。
 * 编辑区为 contenteditable pre + 语法高亮（单层，选中天然对齐）。
 */
import { computed, ref, onBeforeUnmount, watch } from 'vue'
import { highlightCode, langFromFilename } from '../utils/hljs.js'
import { captureEditableState, rehighlightEditable } from '../utils/editable.js'

const props = defineProps({
  /** @type {{name:string, content:string}[]} */
  modelValue: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
  minHeight: { type: String, default: '280px' }
})

const emit = defineEmits(['update:modelValue'])

const NAME_RE = /^[A-Za-z0-9_.-]{1,64}$/

const activeName = ref('')
const notice = ref('')
const newName = ref('')
const fileInput = ref(null)

const files = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const activeFile = computed(() => files.value.find((f) => f.name === activeName.value) || null)

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

function getHighlightedHtml(text, filename) {
  const lang = langFromFilename(filename)
  return highlightCode(text, lang) || escapeHtml(text)
}

function rehighlight() {
  if (!area.value || !activeFile.value) return
  const state = captureEditableState(area.value)
  isInternalUpdate = true
  rehighlightEditable(area.value, getHighlightedHtml(area.value.textContent || '', activeFile.value.name), state)
  isInternalUpdate = false
}

function onInput() {
  if (isComposing || isInternalUpdate || !area.value) return
  updateContent(area.value.textContent || '')
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

/** 把某个文件的内容画进编辑区（换文件时重置滚动，不保留上一个文件的选区） */
function renderActive(f) {
  if (!area.value || !f) return
  isInternalUpdate = true
  rehighlightEditable(area.value, getHighlightedHtml(f.content, f.name), null)
  area.value.scrollTop = 0
  area.value.scrollLeft = 0
  isInternalUpdate = false
}

// 只盯「文件名」：盯 activeFile 对象的话，每次输入都会生成新对象 → 回调重写 innerHTML → 光标被打断。
// flush:'post' 等 DOM 更新完再画：第一次打开时编辑区是 v-if 新建的，pre-flush 阶段 area 还是 null。
watch(
  () => (activeFile.value ? activeFile.value.name : ''),
  (name) => {
    if (name) renderActive(activeFile.value)
  },
  { flush: 'post', immediate: true }
)

// 文件从父级进来（上传 / 载入示例 / 恢复草稿）时，自动选中第一个可用文件，
// 避免"列表里有文件、编辑区却不显示内容"。
watch(
  () => props.modelValue.map((f) => f.name).join('\n'),
  () => {
    const list = props.modelValue
    if (!list.length) {
      activeName.value = ''
      return
    }
    if (!list.some((f) => f.name === activeName.value)) activeName.value = list[0].name
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  clearTimeout(rehighlightTimer)
})

function setNotice(text) {
  notice.value = text
  if (text) setTimeout(() => { if (notice.value === text) notice.value = '' }, 4000)
}

function select(name) {
  activeName.value = name
}

function updateContent(v) {
  files.value = files.value.map((f) => (f.name === activeName.value ? { ...f, content: v } : f))
}

function removeFile(name) {
  files.value = files.value.filter((f) => f.name !== name)
  if (activeName.value === name) {
    activeName.value = files.value.length ? files.value[0].name : ''
  }
}

function pickFiles() {
  if (fileInput.value) fileInput.value.click()
}

async function onFilesChosen(e) {
  const list = Array.from(e.target.files || [])
  e.target.value = ''
  if (!list.length) return
  let added = 0
  for (const file of list) {
    const name = file.name
    if (!NAME_RE.test(name) || name === '.' || name === '..') {
      setNotice(`跳过 ${name}：文件名仅限字母、数字、_ . -，最长 64 字符`)
      continue
    }
    if (files.value.some((f) => f.name === name)) {
      setNotice(`跳过 ${name}：文件名重复`)
      continue
    }
    const content = await file.text()
    if (!content.trim()) {
      setNotice(`跳过 ${name}：文件内容为空`)
      continue
    }
    files.value = [...files.value, { name, content }]
    activeName.value = name
    added++
  }
  if (added) setNotice(`已添加 ${added} 个文件`)
}

function addEmptyFile() {
  const name = newName.value.trim()
  if (!NAME_RE.test(name) || name === '.' || name === '..') {
    setNotice('文件名仅限字母、数字、_ . -，最长 64 字符')
    return
  }
  if (files.value.some((f) => f.name === name)) {
    setNotice(`文件名重复：${name}`)
    return
  }
  files.value = [...files.value, { name, content: '' }]
  activeName.value = name
  newName.value = ''
}

function fileSize(content) {
  const n = new Blob([content]).size
  return n < 1024 ? `${n} B` : `${(n / 1024).toFixed(1)} KB`
}
</script>

<template>
  <div class="mfile">
    <div class="mfile__bar">
      <span class="mfile__title mono-data">多文件 · {{ files.length }} 个</span>
      <div class="mfile__actions">
        <button
          type="button"
          class="mfile__btn"
          :disabled="disabled"
          @click="pickFiles"
        >[ 上传文件 ]</button>
        <input
          ref="fileInput"
          class="sr-only"
          type="file"
          multiple
          @change="onFilesChosen"
        />
      </div>
    </div>

    <p v-if="notice" class="mfile__notice caption" aria-live="polite">{{ notice }}</p>

    <!-- 文件列表 -->
    <ul v-if="files.length" class="mfile__list" aria-label="提交文件列表">
      <li
        v-for="f in files"
        :key="f.name"
        class="mfile__item"
        :class="{ 'mfile__item--active': f.name === activeName }"
      >
        <button
          type="button"
          class="mfile__name mono-data"
          :disabled="disabled"
          :aria-pressed="f.name === activeName"
          @click="select(f.name)"
        >
          <span aria-hidden="true">{{ f.name === activeName ? '●' : '○' }}</span>
          {{ f.name }}
        </button>
        <span class="mfile__size mono-data">{{ fileSize(f.content) }}</span>
        <button
          type="button"
          class="mfile__del"
          :disabled="disabled"
          :aria-label="`删除文件 ${f.name}`"
          @click="removeFile(f.name)"
        >[ 删 ]</button>
      </li>
    </ul>
    <p v-else class="mfile__empty caption">
      还没有文件。点「上传文件」选中多个源码（可含 Makefile / .h），或在下方新建。
    </p>

    <!-- 新建空文件 -->
    <div class="mfile__new">
      <label class="sr-only" for="mfile-new-name">新建文件名</label>
      <input
        id="mfile-new-name"
        v-model="newName"
        class="mfile__input mono-data"
        type="text"
        placeholder="新文件名，如 Makefile"
        :disabled="disabled"
        @keydown.enter.prevent="addEmptyFile"
      />
      <button type="button" class="mfile__btn" :disabled="disabled" @click="addEmptyFile">[ 新建 ]</button>
    </div>

    <!-- 选中文件编辑器（contenteditable + 高亮） -->
    <div v-if="activeFile" class="mfile__editor">
      <div class="mfile__ebar mono-data">$ edit {{ activeFile.name }}</div>
      <div class="mfile__box" :style="{ '--editor-min': minHeight }">
        <div
          ref="area"
          class="mfile__code mfile__hl"
          :contenteditable="!disabled"
          :style="{ minHeight }"
          role="textbox"
          aria-multiline="true"
          :aria-label="`编辑 ${activeFile.name}`"
          spellcheck="false"
          @input="onInput"
          @keydown="onKeydown"
          @paste="onPaste"
          @compositionstart="onCompositionStart"
          @compositionend="onCompositionEnd"
        ></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mfile {
  border: 1px solid var(--code-border);
  background: var(--code-bg);
  border-radius: var(--radius);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
}

.mfile:focus-within {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

.mfile__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.mfile__title {
  color: var(--code-accent);
}

.mfile__btn {
  font-family: var(--font-mono);
  font-size: var(--text-micro);
  color: var(--code-accent);
  background: transparent;
  border: 1px solid var(--code-border);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  cursor: pointer;
}

.mfile__btn:hover:not(:disabled) {
  background: var(--code-bar-bg);
}

.mfile__btn:disabled {
  color: var(--code-muted);
  cursor: not-allowed;
}

.mfile__notice {
  color: var(--code-number);
  margin: 0;
}

.mfile__list {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid var(--code-border);
  border-radius: var(--radius-sm);
  max-height: 180px;
  overflow-y: auto;
}

.mfile__item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 4px var(--space-2);
  border-bottom: 1px solid var(--code-border);
}

.mfile__item:last-child {
  border-bottom: none;
}

.mfile__item--active {
  background: var(--code-bar-bg);
}

.mfile__name {
  flex: 1;
  text-align: left;
  background: none;
  border: none;
  color: var(--code-text);
  cursor: pointer;
  padding: 2px 0;
  min-height: 28px;
}

.mfile__item--active .mfile__name {
  color: var(--code-accent);
}

.mfile__size {
  color: var(--code-muted);
  font-size: var(--text-micro);
}

.mfile__del {
  font-family: var(--font-mono);
  font-size: var(--text-micro);
  color: var(--code-error);
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
}

.mfile__del:hover:not(:disabled) {
  text-decoration: underline;
}

.mfile__empty {
  color: var(--code-muted);
  margin: 0;
}

.mfile__new {
  display: flex;
  gap: var(--space-2);
}

.mfile__input {
  flex: 1;
  min-width: 0;
  height: 32px;
  padding: 0 var(--space-2);
  background: var(--code-bar-bg);
  border: 1px solid var(--code-border);
  border-radius: var(--radius-sm);
  color: var(--code-text);
}

.mfile__input::placeholder {
  color: var(--code-muted);
}

.mfile__editor {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--code-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.mfile__ebar {
  padding: 4px var(--space-2);
  background: var(--code-bar-bg);
  color: var(--code-accent);
  font-size: var(--text-micro);
}

/* contenteditable 编辑区（单层，选中天然对齐） */
.mfile__code {
  display: block;
  margin: 0;
  padding: var(--space-3);
  font-family: var(--font-mono);
  font-size: var(--text-mono-code);
  /* 整数行高：避免 13px × 1.65 = 21.45px 的半像素行盒在长文件里累积错位 */
  line-height: 21px;
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
  min-height: var(--editor-min, 280px);
}

</style>
