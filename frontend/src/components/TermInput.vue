<script setup>
/**
 * 终端风输入（Δ2-1 TermInput）：标签行 `$ 字段名`（$ 用 --primary，真 label for），
 * 输入框同 FileListEditor 输入语言（--code-bar-bg 底）；聚焦绿描边；
 * 错误态 --danger-text 边 + 下方红字，aria-invalid + aria-describedby。
 */
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  /** 标签文字（渲染为 `$ {label}`） */
  label: { type: String, required: true },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  /** 错误语（非空即错误态） */
  error: { type: String, default: '' },
  autocomplete: { type: String, default: '' },
  name: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue'])

const uid = `term-${Math.random().toString(36).slice(2, 9)}`
const errId = `${uid}-err`

const value = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})
</script>

<template>
  <div class="term">
    <label class="term__label" :for="uid">
      <span class="term__prompt" aria-hidden="true">$</span>
      <span class="term__name">{{ label }}</span>
    </label>
    <input
      :id="uid"
      v-model="value"
      class="term__input"
      :class="{ 'term__input--error': !!error }"
      :type="type"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      :name="name"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="error ? errId : undefined"
    />
    <p v-if="error" :id="errId" class="term__err" role="alert">{{ error }}</p>
  </div>
</template>

<style scoped>
.term {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.term__label {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  min-height: 24px;
}

.term__prompt {
  color: var(--primary);
  font-weight: 700;
}

.term__input {
  height: var(--control-h);
  padding: 0 var(--space-3);
  background: var(--code-bar-bg);
  border: 1px solid var(--code-border);
  border-radius: var(--radius-sm);
  color: var(--code-text);
  caret-color: var(--code-accent);
  font-family: var(--font-mono);
  font-size: var(--text-mono-code);
}

.term__input::placeholder {
  color: var(--code-muted);
}

.term__input:focus {
  border-color: var(--primary);
  outline: none;
}

.term__input:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

.term__input--error {
  border-color: var(--danger-text);
}

.term__err {
  font-size: 12px;
  color: var(--danger-text);
}
</style>
