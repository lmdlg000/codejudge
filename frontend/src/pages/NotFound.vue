<script setup>
/** 404 页：content-plan 第 7 节要求含「回到题目列表」入口 */
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import EmptyState from '../components/EmptyState.vue'
import { applyTdk } from '../utils/tdk.js'

const router = useRouter()

onMounted(() => {
  applyTdk({
    title: '页面不存在 | CodeJudge',
    description: '访问的页面不存在。回到题目列表继续作答。'
  })
})
</script>

<template>
  <main class="page">
    <div class="page__main container">
      <!-- SEO/无障碍：404 页也保持唯一 H1（sr-only，不改变视觉） -->
      <h1 class="sr-only">页面不存在</h1>
      <EmptyState
        illustration="puzzle"
        illustration-title="页面不存在示意图"
        text="页面不存在。回到题目列表选一道题继续。"
        action-label="回到题目列表"
        @action="router.push('/')"
      />
    </div>
  </main>
</template>
