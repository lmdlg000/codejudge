<script setup>
/**
 * 登录成功 Toast（Δ2-1）：视口右下、2.4s 自动消失、aria-live=polite。
 */
import { useToast } from '../composables/useToast.js'

const { message, visible, hide } = useToast()
</script>

<template>
  <div
    v-if="visible"
    class="toast"
    role="status"
    aria-live="polite"
  >
    <span class="toast__text">{{ message }}</span>
    <button type="button" class="toast__close" aria-label="关闭提示" @click="hide">×</button>
  </div>
</template>

<style scoped>
.toast {
  position: fixed;
  right: var(--space-6);
  bottom: var(--space-6);
  z-index: var(--z-toast);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  max-width: min(360px, calc(100vw - 32px));
  padding: var(--space-3) var(--space-4);
  background: var(--bg-surface);
  border: 1px solid var(--success-border);
  border-left: 3px solid var(--success-text);
  border-radius: var(--radius);
  box-shadow: var(--shadow-1);
  color: var(--success-text);
  font-size: var(--text-body);
}

.toast__text {
  flex: 1;
}

.toast__close {
  flex: none;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  border-radius: var(--radius-sm);
}

.toast__close:hover {
  background: var(--bg-subtle);
  color: var(--text-primary);
}

@media (max-width: 640px) {
  .toast {
    right: var(--space-4);
    bottom: var(--space-4);
  }
}
</style>
