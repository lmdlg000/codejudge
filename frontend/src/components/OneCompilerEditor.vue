<script setup>
/**
 * OneCompiler 嵌入式编辑器组件（supabase 模式代码测试面）。
 * 协议（https://onecompiler.github.io/editor-embed-demo/complex-editor.html）：
 *   父→iframe：{ eventType:'populateCode', language, files, stdin, result } / { eventType:'triggerRun' }
 *   iframe→父：onmessage，e.data 为代码对象 { language, files, stdin, result? }（codeChangeEvent）
 * 能力：代码变更回传（提交载荷来源）、逐样例注入 stdin 并触发运行、等待运行结果（best-effort）。
 */
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  /** 初始代码（单文件） */
  modelValue: { type: String, default: '' },
  /** 高度 */
  height: { type: String, default: '520px' },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])

const frameEl = ref(null)
const ready = ref(false)

const EMBED_SRC =
  'https://onecompiler.com/embed/cpp' +
  '?codeChangeEvent=true&listenToEvents=true&theme=dark' +
  '&hideLanguageSelection=true&hideTitle=true&hideNew=true'

/** 等待一次带 result 的回传（triggerRun 后） */
let pendingResolve = null
let pendingTimer = null

function post(obj) {
  const w = frameEl.value && frameEl.value.contentWindow
  if (!w) return false
  w.postMessage(obj, '*')
  return true
}

/** 注入代码（+可选 stdin） */
function populate(code, stdin) {
  return post({
    eventType: 'populateCode',
    language: 'cpp',
    files: [{ name: 'main.cpp', content: code ?? props.modelValue }],
    stdin: stdin ?? ''
  })
}

/** 触发编辑器内运行 */
function triggerRun() {
  return post({ eventType: 'triggerRun' })
}

/**
 * 用指定样例入参在编辑器内测试（注入 stdin → 触发运行 → 等待结果回传）。
 * 返回 { stdout, stderr, status } 或 null（20s 内未收到 result 回传）。
 */
async function runWithStdin(stdin) {
  if (!ready.value) return null
  populate(props.modelValue, stdin)
  await new Promise((r) => setTimeout(r, 300))
  return await new Promise((resolve) => {
    pendingResolve = resolve
    clearTimeout(pendingTimer)
    pendingTimer = setTimeout(() => {
      pendingResolve = null
      resolve(null)
    }, 20000)
    triggerRun()
  })
}

defineExpose({ runWithStdin, populate, triggerRun })

function onMessage(e) {
  const d = e.data
  if (!d || typeof d !== 'object') return
  if (d.language && d.files) {
    // 代码对象回传：同步最新代码（取第一个文件内容）
    ready.value = true
    const content = (d.files[0] && d.files[0].content) || ''
    if (content !== props.modelValue) emit('update:modelValue', content)
    // 带 result 的回传：resolve 等待中的 runWithStdin
    if (d.result && pendingResolve) {
      const r = d.result
      const resolve = pendingResolve
      pendingResolve = null
      clearTimeout(pendingTimer)
      resolve({
        stdout: String(r.stdout ?? r.output ?? ''),
        stderr: String(r.stderr ?? r.error ?? ''),
        status: String(r.status ?? '')
      })
    }
    return
  }
  if (d.eventType === 'editorLoaded' || d.eventType) ready.value = true
}

watch(
  () => props.modelValue,
  (v) => {
    // 外部重置（如切换示例）时同步进编辑器
    if (ready.value && v != null) populate(v)
  }
)

onMounted(() => window.addEventListener('message', onMessage))
onBeforeUnmount(() => {
  window.removeEventListener('message', onMessage)
  clearTimeout(pendingTimer)
})
</script>

<template>
  <div class="oc-editor" :style="{ '--oc-h': height }">
    <div class="oc-editor__bar">
      <span class="mono-data oc-editor__title">$ onecompiler editor · cpp</span>
      <span class="caption oc-editor__hint">改动代码自动回传；「测此样例」注入输入并触发运行</span>
    </div>
    <iframe
      ref="frameEl"
      class="oc-editor__frame"
      :src="EMBED_SRC"
      title="OneCompiler 嵌入式编辑器"
      allow="clipboard-write"
    ></iframe>
  </div>
</template>

<style scoped>
.oc-editor {
  border: 1px solid var(--code-border);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--code-bg);
}

.oc-editor__bar {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  padding: 0 var(--space-3);
  background: var(--code-bar-bg);
  flex-wrap: wrap;
}

.oc-editor__title {
  color: var(--code-accent);
  font-size: var(--text-micro);
}

.oc-editor__hint {
  color: var(--code-muted);
}

.oc-editor__frame {
  display: block;
  width: 100%;
  height: var(--oc-h, 520px);
  border: none;
}
</style>
