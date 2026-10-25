<script setup>
/**
 * 按钮（design-spec 5.1）：主/次/危险/文字/图标 五角色 × default/hover/active/disabled/loading。
 * loading 时保持主色 + 16px 旋转环，disabled + aria-busy，不可重复点击。
 */
defineProps({
  variant: {
    type: String,
    default: 'primary' // primary | secondary | danger | text | icon | oauth
  },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  type: { type: String, default: 'button' },
  block: { type: Boolean, default: false },
  /** 图标按钮的无障碍名 */
  ariaLabel: { type: String, default: '' },
  title: { type: String, default: '' }
})
</script>

<template>
  <button
    :type="type"
    class="btn"
    :class="[
      `btn--${variant}`,
      { 'btn--loading': loading, 'btn--block': block }
    ]"
    :disabled="disabled || loading"
    :aria-busy="loading ? 'true' : undefined"
    :aria-label="ariaLabel || undefined"
    :title="title || undefined"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="btn__spinner" aria-hidden="true"></span>
    <span class="btn__label"><slot /></span>
  </button>
</template>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: var(--control-h);
  padding: 0 var(--space-4);
  border-radius: var(--radius);
  border: 1px solid transparent;
  font-size: 14px;
  font-weight: 600;
  line-height: 1;
  cursor: pointer;
  transition: background-color var(--dur-fast) var(--ease-out),
    border-color var(--dur-fast) var(--ease-out),
    color var(--dur-fast) var(--ease-out);
  /* 最小触达 44px：用伪元素扩热区（视觉可 32/40） */
  position: relative;
}

.btn::after {
  content: '';
  position: absolute;
  inset: 50% auto auto 50%;
  width: 100%;
  height: 100%;
  min-width: 44px;
  min-height: 44px;
  transform: translate(-50%, -50%);
}

.btn--block {
  width: 100%;
}

/* —— 主按钮（终端风：绿框描边，hover 反色）—— */
.btn--primary {
  height: var(--control-h-lg);
  padding: 0 var(--space-5);
  font-size: 15px;
  background: var(--primary-bg);
  color: var(--primary);
  border: 1px solid var(--primary);
}
.btn--primary .btn__label::before { content: '[ '; }
.btn--primary .btn__label::after { content: ' ]'; }
.btn--primary:hover:not(:disabled) {
  background: var(--primary);
  color: var(--text-inverse);
}
.btn--primary:active:not(:disabled) {
  background: var(--primary-active);
  color: var(--text-inverse);
  transform: translateY(1px);
}
.btn--primary:disabled:not(.btn--loading) {
  background: var(--bg-subtle);
  border-color: var(--text-disabled);
  color: var(--text-disabled);
  cursor: not-allowed;
}
.btn--primary.btn--loading {
  background: var(--primary-bg);
  border-color: var(--primary);
  color: var(--primary);
  cursor: progress;
}

/* —— 次按钮 —— */
.btn--secondary {
  background: var(--bg-surface);
  color: var(--text-primary);
  border: var(--border-strong);
}
.btn--secondary .btn__label::before { content: '[ '; }
.btn--secondary .btn__label::after { content: ' ]'; }
.btn--secondary:hover:not(:disabled) {
  background: var(--bg-subtle);
  border-color: var(--primary);
  color: var(--primary);
}
.btn--secondary:active:not(:disabled) {
  background: var(--bg-inset);
}
.btn--secondary:disabled {
  color: var(--text-disabled);
  border: var(--border);
  background: var(--bg-subtle);
  cursor: not-allowed;
}

/* —— 危险按钮 —— */
.btn--danger {
  background: var(--danger-solid);
  color: var(--text-inverse);
}
.btn--danger .btn__label::before { content: '[ '; }
.btn--danger .btn__label::after { content: ' ]'; }
.btn--danger:hover:not(:disabled) {
  background: var(--danger-solid-hover);
}
.btn--danger:active:not(:disabled) {
  background: var(--danger-text);
}
.btn--danger:disabled {
  background: var(--bg-subtle);
  color: var(--text-disabled);
  cursor: not-allowed;
}

/* —— 文字按钮 —— */
.btn--text {
  height: var(--control-h-sm);
  padding: 0 var(--space-2);
  background: transparent;
  color: var(--primary);
  border: none;
  font-weight: 500;
}
.btn--text:hover:not(:disabled) {
  color: var(--primary-hover);
  background: var(--primary-bg);
}
.btn--text:active:not(:disabled) {
  color: var(--primary-active);
}
.btn--text:disabled {
  color: var(--text-disabled);
  cursor: not-allowed;
}

/* —— 图标按钮 —— */
.btn--icon {
  width: var(--control-h-sm);
  height: var(--control-h-sm);
  padding: 0;
  background: transparent;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
}
.btn--icon:hover:not(:disabled) {
  background: var(--bg-subtle);
  color: var(--text-primary);
}
.btn--icon:active:not(:disabled) {
  background: var(--bg-inset);
}
.btn--icon:disabled {
  color: var(--text-disabled);
  cursor: not-allowed;
}

/* —— OAuth 按钮（Δ2-1：深底 + GitHub 标，不加 [ ] 括钮）—— */
.btn--oauth {
  height: var(--control-h-lg);
  padding: 0 var(--space-5);
  font-size: 15px;
  background: var(--bg-inset);
  color: var(--text-primary);
  border: 1px solid var(--border-strong);
}
.btn--oauth:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
}
.btn--oauth:active:not(:disabled) {
  background: var(--primary-bg);
}
.btn--oauth:disabled {
  color: var(--text-disabled);
  border-color: var(--border);
  background: var(--bg-subtle);
  cursor: not-allowed;
}

/* —— loading 旋转环（终端绿）—— */
.btn__spinner {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid rgba(214, 232, 216, 0.35);
  border-top-color: var(--text-inverse);
  animation: btn-spin 0.8s linear infinite;
  flex: none;
}

.btn--primary .btn__spinner,
.btn--secondary .btn__spinner,
.btn--text .btn__spinner {
  border-color: rgba(61, 255, 122, 0.35);
  border-top-color: var(--primary);
}

@keyframes btn-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .btn__spinner {
    animation-duration: 1.2s;
  }
}
</style>
