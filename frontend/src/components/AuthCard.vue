<script setup>
/**
 * 终端对话框壳（Δ2-1 AuthCard）：登录/注册表单卡片与退出二次确认共用。
 * 标题条 36px（--code-bar-bg，mono --code-accent 标题 + 8px 绿点装饰）；
 * 顶部 `$ auth --login` 提示符行 + 闪烁光标块。
 */
defineProps({
  /** 标题条文字：auth · login / auth · signup / auth · signout */
  title: { type: String, default: 'auth · login' },
  /** 提示符行：$ auth --login */
  prompt: { type: String, default: '$ auth --login' }
})
</script>

<template>
  <div class="authcard">
    <div class="authcard__bar">
      <span class="authcard__bar-title">{{ title }}</span>
      <span class="authcard__dot" aria-hidden="true"></span>
    </div>
    <div class="authcard__body">
      <p class="authcard__prompt">
        {{ prompt }}<span class="authcard__cursor" aria-hidden="true"></span>
      </p>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.authcard {
  width: min(440px, 100%);
  margin: 0 auto;
  background: var(--bg-surface);
  border: var(--border-strong);
  border-radius: var(--radius);
  box-shadow: var(--shadow-1);
  overflow: hidden;
}

.authcard__bar {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-3);
  background: var(--code-bar-bg);
  border-bottom: 1px solid var(--code-border);
}

.authcard__bar-title {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--code-accent);
  letter-spacing: 0.04em;
}

.authcard__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success-text);
}

.authcard__body {
  padding: var(--space-5) var(--space-5) var(--space-6);
}

.authcard__prompt {
  font-family: var(--font-mono);
  font-size: var(--text-mono-code);
  color: var(--code-muted);
  margin-bottom: var(--space-4);
  display: flex;
  align-items: center;
  gap: 2px;
}

.authcard__cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background: var(--primary);
  animation: auth-blink 1.2s step-end infinite;
}

@keyframes auth-blink {
  50% { opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .authcard__cursor {
    animation: none;
  }
}
</style>
