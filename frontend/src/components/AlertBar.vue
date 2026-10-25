<script setup>
/**
 * 提示条 / 错误条（design-spec 5.10）。
 * 4 语义：success ✓ / warning ▲ / error ✕ / info ℹ（图标形状区分，色弱可用）。
 * 8 错误码 + 网络兜底 → tone 映射见 api/errors.js。
 */
import { computed } from 'vue'
import { ERROR_HINTS } from '../api/errors.js'

const props = defineProps({
  /** 错误码（可选，给定后自动取 content-plan 5.1 文案） */
  code: { type: String, default: '' },
  /** 自定义主提示（不给 code 时用） */
  message: { type: String, default: '' },
  /** 自定义补充行 */
  extra: { type: String, default: '' },
  /** success | warning | error | info */
  tone: { type: String, default: 'error' },
  /** 自定义标题（可选） */
  title: { type: String, default: '' },
  /**
   * 自定义动作按钮文案（Δ2 扩展）。
   * 给定时显示该文案并 emit action(actionKey || 'custom')；
   * 不给时走 ERROR_HINTS 内置动作路径（goto-problems 等），行为不变。
   */
  actionLabel: { type: String, default: '' },
  /** 自定义动作 key（随 action 事件回传，默认 'custom'） */
  actionKey: { type: String, default: '' }
})

const emit = defineEmits(['action'])

const meta = computed(() => (props.code ? ERROR_HINTS[props.code] : null))
const mainText = computed(() => props.message || (meta.value ? meta.value.hint : ''))
const extraText = computed(() => props.extra || (meta.value ? meta.value.extra : ''))
const toneValue = computed(() => props.tone || (meta.value ? meta.value.tone : 'error'))
const builtinActionKey = computed(() => (meta.value ? meta.value.action : null))

/** 按钮文案：外部自定义优先，否则内置动作映射 */
const actionLabel = computed(() => {
  if (props.actionLabel) return props.actionLabel
  switch (builtinActionKey.value) {
    case 'goto-problems':
      return '回到题目列表'
    case 'goto-submissions':
      return '回到提交历史'
    case 'goto-about':
      return '查看使用说明'
    case 'reload':
      return '刷新页面'
    case 'goto-login':
      return '去登录'
    default:
      return ''
  }
})

/** 实际 emit 的动作 key：自定义时用 props.actionKey，否则内置 key */
const emitKey = computed(() => {
  if (props.actionLabel) return props.actionKey || 'custom'
  return builtinActionKey.value
})

const iconPath = computed(() => {
  switch (toneValue.value) {
    case 'success':
      return 'M3 8.5l3.2 3.2L13 5'
    case 'warning':
      return 'M8 2.5L14.5 13.5h-13L8 2.5zM8 6.5v3.2M8 11.6v.4'
    case 'info':
      return 'M8 7.2v4.2M8 4.6v.4M14 8A6 6 0 112 8a6 6 0 0112 0z'
    default:
      return 'M4.5 4.5l7 7M11.5 4.5l-7 7'
  }
})
</script>

<template>
  <div
    class="alert"
    :class="`alert--${toneValue}`"
    role="alert"
    aria-live="polite"
  >
    <svg
      class="alert__icon"
      viewBox="0 0 16 16"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <path :d="iconPath" />
    </svg>
    <div class="alert__body">
      <p v-if="title" class="alert__title">{{ title }}</p>
      <p class="alert__main">{{ mainText }}</p>
      <p v-if="extraText" class="alert__extra">{{ extraText }}</p>
      <slot />
    </div>
    <button
      v-if="actionLabel"
      type="button"
      class="alert__action"
      @click="emit('action', emitKey)"
    >{{ actionLabel }}</button>
  </div>
</template>

<style scoped>
.alert {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius);
  border: 1px solid;
  border-left: 3px solid;
}

.alert__icon {
  flex: none;
  margin-top: 2px;
}

.alert__body {
  flex: 1;
  min-width: 0;
}

.alert__title {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.5;
}

.alert__main {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.5;
}

.alert__extra {
  margin-top: 2px;
  font-size: var(--text-caption);
  line-height: var(--lh-caption);
  color: inherit;
  opacity: 0.85;
}

.alert__action {
  flex: none;
  height: var(--control-h-sm);
  padding: 0 var(--space-3);
  border-radius: var(--radius-sm);
  border: 1px solid currentColor;
  background: transparent;
  color: inherit;
  font-size: var(--text-caption);
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.alert__action:hover {
  background: rgba(15, 23, 42, 0.06);
}

.alert--success {
  background: var(--success-bg);
  color: var(--success-text);
  border-color: var(--success-border);
  border-left-color: var(--success-text);
}

.alert--warning {
  background: var(--warning-bg);
  color: var(--warning-text);
  border-color: var(--warning-border);
  border-left-color: var(--warning-text);
}

.alert--error {
  background: var(--danger-bg);
  color: var(--danger-text);
  border-color: var(--danger-border);
  border-left-color: var(--danger-text);
}

.alert--info {
  background: var(--info-bg);
  color: var(--info-text);
  border-color: var(--info-border);
  border-left-color: var(--info-text);
}
</style>
