<script setup>
/**
 * 错误提示条：输入 ApiError（或 {code}），文案取 content-plan 5.1，
 * 动作按钮按场景路由（回到题目列表 / 刷新页面 / 查看使用说明 / 回到提交历史）。
 */
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AlertBar from './AlertBar.vue'

const props = defineProps({
  /** ApiError 实例或 {code, hint, extra, tone, action} */
  error: { type: [Object, String], default: null },
  /** 覆盖动作（goto-problems / goto-submissions / goto-about / goto-login / reload / retry） */
  actionOverride: { type: String, default: '' }
})

const emit = defineEmits(['action'])
const router = useRouter()
const route = useRoute()

const code = computed(() =>
  typeof props.error === 'string' ? props.error : (props.error && props.error.code) || ''
)

function onAction(key) {
  emit('action', key)
  switch (key) {
    case 'goto-problems':
      router.push('/')
      break
    case 'goto-submissions':
      router.push('/submissions')
      break
    case 'goto-about':
      router.push('/about')
      break
    case 'goto-login':
      router.push({ path: '/login', query: { redirect: route.fullPath } })
      break
    case 'reload':
      window.location.reload()
      break
    default:
      break
  }
}
</script>

<template>
  <AlertBar
    v-if="code"
    :code="code"
    :message="typeof error === 'object' && error && error.message ? error.message : ''"
    :tone="typeof error === 'object' && error && error.tone ? error.tone : 'error'"
    @action="onAction"
  />
</template>
