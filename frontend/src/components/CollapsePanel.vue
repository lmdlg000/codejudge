<script setup>
/**
 * 折叠面板（design-spec 5.12）。
 * 文字按钮 + chevron（展开转 180°）；aria-expanded / aria-controls 必须有；
 * 面板体 max-height 过渡，prefers-reduced-motion 时无动画。
 */
import { ref, watch } from 'vue'

const props = defineProps({
  /** 折叠按钮文案（展开态） */
  openLabel: { type: String, default: '展开' },
  /** 折叠按钮文案（收起态） */
  closeLabel: { type: String, default: '收起' },
  /** 默认是否展开 */
  defaultOpen: { type: Boolean, default: false },
  /** 面板标题（可选，H4） */
  title: { type: String, default: '' },
  /** 说明行（可选） */
  caption: { type: String, default: '' },
  /** 面板体最大高度 */
  maxHeight: { type: String, default: '320px' }
})

const open = ref(props.defaultOpen)
const uid = `collapse-${Math.random().toString(36).slice(2, 9)}`

watch(
  () => props.defaultOpen,
  (v) => {
    open.value = v
  }
)

function toggle() {
  open.value = !open.value
}
</script>

<template>
  <div class="collapse">
    <div v-if="title || caption" class="collapse__head">
      <h4 v-if="title" class="collapse__title">{{ title }}</h4>
      <p v-if="caption" class="collapse__caption caption">{{ caption }}</p>
    </div>
    <button
      type="button"
      class="collapse__trigger"
      :aria-expanded="open ? 'true' : 'false'"
      :aria-controls="uid"
      @click="toggle"
    >
      <svg
        class="collapse__chevron"
        :class="{ 'collapse__chevron--open': open }"
        width="12"
        height="12"
        viewBox="0 0 12 12"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M2.5 4.5L6 8l3.5-3.5" />
      </svg>
      <span>{{ open ? closeLabel : openLabel }}</span>
    </button>
    <div
      v-show="open"
      :id="uid"
      class="collapse__panel"
      :style="{ '--panel-max': maxHeight }"
    >
      <slot />
    </div>
  </div>
</template>

<style scoped>
.collapse__head {
  margin-bottom: var(--space-2);
}

.collapse__title {
  margin: 0;
}

.collapse__caption {
  margin-top: var(--space-1);
  color: var(--text-secondary);
}

.collapse__trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  height: var(--control-h-sm);
  padding: 0 var(--space-2);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  position: relative;
}

/* 扩热区到 44px */
.collapse__trigger::after {
  content: '';
  position: absolute;
  inset: 50% auto auto 50%;
  width: 100%;
  height: 44px;
  min-width: 44px;
  transform: translate(-50%, -50%);
}

.collapse__trigger:hover {
  color: var(--primary-hover);
  background: var(--primary-bg);
}

.collapse__chevron {
  transition: transform var(--dur-fast) var(--ease-out);
}

.collapse__chevron--open {
  transform: rotate(180deg);
}

.collapse__panel {
  margin-top: var(--space-2);
  max-height: none;
}
</style>
