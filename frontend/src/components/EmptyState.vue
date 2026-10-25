<script setup>
/**
 * 空状态（design-spec 5.11 / content-plan 5.2）。
 * 240×160 内联 SVG 插图 + 一句话 + 一个主按钮出路。
 * 三处固定文案由调用方传入（逐字取 content-plan）。
 */
import AppButton from './AppButton.vue'

defineProps({
  /** SVG 说明一句话（role=img + title） */
  illustrationTitle: { type: String, default: '空状态示意图' },
  /** 空收件箱 | 错误拼图 | SE 扳手 */
  illustration: { type: String, default: 'inbox' },
  text: { type: String, required: true },
  actionLabel: { type: String, default: '' }
})

const emit = defineEmits(['action'])
</script>

<template>
  <div class="empty">
    <!-- 9.5 空收件箱 -->
    <svg
      v-if="illustration === 'inbox'"
      class="empty__art"
      viewBox="0 0 240 160"
      width="240"
      height="160"
      role="img"
      :aria-label="illustrationTitle"
    >
      <title>{{ illustrationTitle }}</title>
      <rect x="46" y="36" width="148" height="96" rx="8" fill="#101611" stroke="#35513D" stroke-width="2" />
      <path d="M46 88h36l10 16h56l10-16h36" fill="none" stroke="#35513D" stroke-width="2" stroke-linejoin="round" />
      <rect x="150" y="52" width="12" height="22" rx="1" fill="#3DFF7A" />
    </svg>

    <!-- 9.6 错误拼图 -->
    <svg
      v-else-if="illustration === 'puzzle'"
      class="empty__art"
      viewBox="0 0 240 160"
      width="240"
      height="160"
      role="img"
      :aria-label="illustrationTitle"
    >
      <title>{{ illustrationTitle }}</title>
      <rect x="36" y="40" width="72" height="72" rx="6" fill="#101611" stroke="#35513D" stroke-width="2" />
      <rect x="132" y="40" width="72" height="72" rx="6" fill="#101611" stroke="#35513D" stroke-width="2" />
      <path d="M112 62l6 6M112 84l6-6" stroke="#FF5F56" stroke-width="2" stroke-linecap="round" />
      <circle cx="188" cy="116" r="12" fill="#2B0F0C" />
      <path d="M183 111l10 10M193 111l-10 10" stroke="#FF5F56" stroke-width="2" stroke-linecap="round" />
    </svg>

    <!-- 9.7 SE 扳手 -->
    <svg
      v-else
      class="empty__art"
      viewBox="0 0 240 160"
      width="240"
      height="160"
      role="img"
      :aria-label="illustrationTitle"
    >
      <title>{{ illustrationTitle }}</title>
      <path d="M60 110l40-40 14 14-40 40-18 4 4-18z" fill="none" stroke="#35513D" stroke-width="2" stroke-linejoin="round" />
      <path d="M96 66a18 18 0 1124-24l-8 8 8 8 8-8a18 18 0 11-24 24" fill="none" stroke="#35513D" stroke-width="2" />
      <path d="M150 52l30 52h-60l30-52z" fill="#2B2006" stroke="#FFB000" stroke-width="2" stroke-linejoin="round" />
      <path d="M150 70v18M150 96v2" stroke="#FFB000" stroke-width="2" stroke-linecap="round" />
    </svg>

    <p class="empty__text">{{ text }}</p>
    <AppButton v-if="actionLabel" variant="primary" @click="emit('action')">
      {{ actionLabel }}
    </AppButton>
    <slot />
  </div>
</template>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-12) var(--space-6);
  text-align: center;
}

.empty__art {
  display: block;
}

.empty__text {
  max-width: 420px;
  font-size: var(--text-body);
  line-height: var(--lh-body);
  color: var(--text-secondary);
}
</style>
