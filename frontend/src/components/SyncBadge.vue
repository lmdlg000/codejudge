<script setup>
/**
 * 同步徽章三态（Δ2-3）：徽章语法同 VerdictBadge（22px、左 3px 色条、mono 12px/700）。
 * true=已同步到你的账号（success）；false 带过 token=同步失败，仅保存在本机（warning）
 * + 重试同步；false 未带 token=仅保存在本机（SE 灰）。
 * 无障碍：aria-label + 文字双信道。
 */
import { computed } from 'vue'
import AppButton from './AppButton.vue'

const props = defineProps({
  /** synced 字段（true / false；null/undefined 视为未带 token 的 false） */
  synced: { type: Boolean, default: false },
  /** 本次提交是否携带过 token */
  hadToken: { type: Boolean, default: false },
  /** 重试同步 loading */
  retrying: { type: Boolean, default: false }
})

const emit = defineEmits(['retry'])

const state = computed(() => {
  if (props.synced) return 'synced'
  return props.hadToken ? 'failed' : 'local'
})

const text = computed(() => {
  switch (state.value) {
    case 'synced':
      return '已同步到你的账号'
    case 'failed':
      return '同步失败，仅保存在本机'
    default:
      return '仅保存在本机'
  }
})
</script>

<template>
  <div class="sync">
    <span
      class="sync__badge"
      :class="`sync__badge--${state}`"
      :title="text"
      :aria-label="`同步状态：${text}`"
    >{{ text }}</span>
    <AppButton
      v-if="state === 'failed'"
      variant="text"
      :loading="retrying"
      @click="emit('retry')"
    >{{ retrying ? '同步中…' : '重试同步' }}</AppButton>
    <p v-if="state === 'failed'" class="sync__note caption">
      云端暂不可用，本次结果已存本机 reports/。
    </p>
  </div>
</template>

<style scoped>
.sync {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.sync__badge {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 var(--space-2);
  border-radius: var(--radius-sm);
  border: 1px solid;
  border-left: 3px solid;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
}

/* 已同步：success 三件套（AC 绿） */
.sync__badge--synced {
  color: var(--success-text);
  background: var(--success-bg);
  border-color: var(--success-border);
  border-left-color: var(--success-text);
}

/* 同步失败：warning 三件套（TLE 琥珀） */
.sync__badge--failed {
  color: var(--warning-text);
  background: var(--warning-bg);
  border-color: var(--warning-border);
  border-left-color: var(--warning-text);
}

/* 仅保存在本机：SE 灰三件套 */
.sync__badge--local {
  color: var(--verdict-se-text);
  background: var(--verdict-se-bg);
  border-color: var(--verdict-se-border);
  border-left-color: var(--verdict-se-text);
}

.sync__note {
  flex-basis: 100%;
  color: var(--text-secondary);
  margin: 0;
}
</style>
