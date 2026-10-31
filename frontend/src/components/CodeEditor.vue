<script setup>
/**
 * 代码编辑区（design-spec 5.8，P0 = 等宽 textarea）。
 * 预填 main 骨架；空码时父组件禁用提交；wrap="off" 横向滚动；
 * 焦点容器 2px 焦点环；label 关联（无障碍硬项）。
 */
import { computed } from 'vue'

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
    <textarea
      :id="uid"
      v-model="value"
      class="editor__area"
      :readonly="readonly"
      spellcheck="false"
      wrap="off"
      placeholder="把 main.cpp 的内容贴到这里"
    ></textarea>
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

.editor__area {
  display: block;
  width: 100%;
  min-height: var(--editor-min);
  padding: var(--space-3) var(--space-4);
  border: none;
  resize: vertical;
  background: var(--code-bg);
  color: var(--code-text);
  caret-color: var(--code-accent);
  font-family: var(--font-mono);
  font-size: var(--text-mono-code);
  line-height: var(--lh-mono-code);
  outline: none;
  font-variant-ligatures: none;
  font-feature-settings: "liga" 0, "calt" 0;
}

.editor__area::placeholder {
  color: var(--code-muted);
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
