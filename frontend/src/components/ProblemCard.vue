<script setup>
/**
 * 行式题目卡片（design-spec 5.2）。
 * 整卡可点（<a> 保键盘可达）+ 右侧固定 CTA。
 * 信息位：题号+标题 → 题型·难度（topic/difficulty 可选，缺失不渲染）→ 标签组 → CTA。
 */
import { computed } from 'vue'
import { modeShort } from '../utils/format.js'

const props = defineProps({
  problem: { type: Object, required: true }
})

const p = props.problem

const subline = computed(() => {
  const bits = []
  if (p.topic) bits.push(p.topic)
  if (p.difficulty) bits.push(p.difficulty)
  return bits.join(' · ')
})
</script>

<template>
  <router-link
    :to="`/problems/${p.id}`"
    class="pcard"
  >
    <div class="pcard__main">
      <div class="pcard__row1">
        <span class="pcard__id mono-data">{{ p.id }}</span>
        <h3 class="pcard__title">{{ p.title }}</h3>
      </div>
      <p v-if="subline" class="pcard__sub caption">{{ subline }}</p>
    </div>

    <div class="pcard__aside">
      <ul class="pcard__tags" aria-label="题目信息">
        <li class="tag tag--mode">{{ modeShort(p.contest_type) }}</li>
        <li class="tag tag--num">{{ p.score != null ? p.score : 100 }}分</li>
        <li class="tag tag--num">{{ p.time_limit_ms }}ms</li>
        <li class="tag">用例数 {{ p.test_count }}</li>
      </ul>
      <span class="pcard__cta">去做 {{ p.id }}</span>
    </div>
  </router-link>
</template>

<style scoped>
.pcard {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--bg-surface);
  border: var(--border);
  border-radius: var(--radius);
  color: inherit;
  cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease-out),
    box-shadow var(--dur-fast) var(--ease-out);
}

.pcard:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow-1);
  color: inherit;
}

.pcard:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

.pcard__main {
  min-width: 0;
  flex: 1;
}

.pcard__row1 {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  min-width: 0;
}

.pcard__id {
  flex: none;
  width: 48px;
  color: var(--text-secondary);
  font-weight: 500;
}

.pcard__title {
  font-size: var(--text-h4);
  line-height: var(--lh-h4);
  font-weight: var(--fw-h4);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pcard__sub {
  margin-top: var(--space-1);
  padding-left: calc(48px + var(--space-3));
  color: var(--text-muted);
}

.pcard__aside {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex: none;
}

.pcard__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  list-style: none;
  margin: 0;
  padding: 0;
}

.tag {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--bg-subtle);
  color: var(--text-secondary);
  font-size: var(--text-caption);
  line-height: 1;
  white-space: nowrap;
}

.tag--num {
  font-family: var(--font-mono);
  font-size: var(--text-mono-badge);
  font-weight: 500;
}

.tag--mode {
  background: var(--primary-bg);
  color: var(--primary);
  font-family: var(--font-mono);
  font-size: var(--text-mono-badge);
  font-weight: 700;
}

.pcard__cta {
  display: inline-flex;
  align-items: center;
  height: var(--control-h);
  padding: 0 var(--space-4);
  border-radius: var(--radius);
  background: var(--primary);
  color: var(--text-inverse);
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.pcard:hover .pcard__cta {
  background: var(--primary-hover);
}

@media (max-width: 1023px) {
  .pcard {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-3);
  }

  .pcard__aside {
    justify-content: space-between;
    width: 100%;
  }

  .pcard__sub {
    padding-left: 0;
  }
}
</style>
