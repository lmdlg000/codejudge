<script setup>
/**
 * 统一 tab 组件（Δ2-0/Δ2-1/Δ2-4）：登录|注册 与 云端|本机 共用，
 * 结构沿用 ProblemDetail mode-tabs 现值。
 * 选中态：bg --primary-bg + 文字 --primary + `> ` 前缀；role=tablist/tab，
 * 方向键 roving tabindex（选中 0，未选中 -1）。
 */
import { ref, computed } from 'vue'

const props = defineProps({
  /** [{ key, label }] */
  tabs: { type: Array, required: true },
  modelValue: { type: String, required: true },
  ariaLabel: { type: String, default: '选项卡' }
})

const emit = defineEmits(['update:modelValue'])

const rootEl = ref(null)

const index = computed(() => {
  const i = props.tabs.findIndex((t) => t.key === props.modelValue)
  return i >= 0 ? i : 0
})

function select(key) {
  emit('update:modelValue', key)
}

function onKeydown(e) {
  const n = props.tabs.length
  if (!n) return
  let next = null
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (index.value + 1) % n
  else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (index.value - 1 + n) % n
  else if (e.key === 'Home') next = 0
  else if (e.key === 'End') next = n - 1
  if (next == null) return
  e.preventDefault()
  const key = props.tabs[next].key
  select(key)
  // 焦点跟随选中项
  const root = rootEl.value
  if (root) {
    const btns = root.querySelectorAll('[role="tab"]')
    if (btns[next]) btns[next].focus()
  }
}
</script>

<template>
  <div
    ref="rootEl"
    class="tabs"
    role="tablist"
    :aria-label="ariaLabel"
    @keydown="onKeydown"
  >
    <button
      v-for="(t, i) in tabs"
      :key="t.key"
      type="button"
      class="tabs__tab"
      :class="{ 'tabs__tab--on': t.key === modelValue }"
      role="tab"
      :aria-selected="t.key === modelValue"
      :tabindex="i === index ? 0 : -1"
      @click="select(t.key)"
    >{{ t.label }}</button>
  </div>
</template>

<style scoped>
.tabs {
  display: flex;
  border: var(--border-strong);
  border-radius: var(--radius);
  overflow: hidden;
}

.tabs__tab {
  flex: 1;
  height: 36px;
  padding: 0 var(--space-3);
  background: var(--bg-surface);
  color: var(--text-secondary);
  border: none;
  font-family: inherit;
  font-size: var(--text-caption);
  font-weight: 600;
  cursor: pointer;
  /* 点击区撑满 44px */
  position: relative;
}

.tabs__tab::after {
  content: '';
  position: absolute;
  inset: 50% auto auto 50%;
  width: 100%;
  height: 44px;
  transform: translate(-50%, -50%);
}

.tabs__tab:hover {
  background: var(--bg-subtle);
}

.tabs__tab--on {
  background: var(--primary-bg);
  color: var(--primary);
}

.tabs__tab--on::before {
  content: '> ';
}

.tabs__tab:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: -2px;
}
</style>
