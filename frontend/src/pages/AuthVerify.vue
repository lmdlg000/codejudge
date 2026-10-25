<script setup>
/**
 * 邮箱验证落地页 /auth/verified。
 * 入口：注册后 Supabase 确认邮件的 ConfirmationURL → 验证通过 302 回站点（?verified=1）
 *      → useAuth.initAuth 检测后 router.replace 到本页；
 *      链接过期/无效（hash 带 error=）→ 本页失败态。
 */
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import { isLoggedIn, displayName } from '../composables/useAuth.js'
import { applyTdk } from '../utils/tdk.js'

const route = useRoute()
const router = useRouter()
const failed = computed(() => route.query.failed === '1')

onMounted(() => {
  applyTdk({
    title: failed.value ? '验证未通过 · CodeJudge' : '邮箱验证成功 · CodeJudge',
    description: failed.value
      ? '验证链接已过期或无效，请重新注册或联系管理员。'
      : '邮箱验证成功，现在可以登录并开始做题了。'
  })
})
</script>

<template>
  <main class="page">
    <div class="page__main container container--narrow verify">
      <template v-if="!failed">
        <div class="verify__mark" aria-hidden="true">✓</div>
        <h1>邮箱验证成功</h1>
        <p class="verify__lead">
          {{ isLoggedIn ? `${displayName || '你'}，账号已就绪，直接开始做题吧。` : '账号已激活，登录后即可提交判题、同步历史。' }}
        </p>
        <div class="verify__actions">
          <AppButton variant="primary" @click="router.push(isLoggedIn ? '/' : '/login')">
            {{ isLoggedIn ? '进入题库' : '去登录' }}
          </AppButton>
          <AppButton variant="secondary" @click="router.push('/about')">先看看使用说明</AppButton>
        </div>
      </template>
      <template v-else>
        <div class="verify__mark verify__mark--fail" aria-hidden="true">!</div>
        <h1>验证未通过</h1>
        <p class="verify__lead">
          验证链接已过期或无效（确认邮件有时效）。请重新注册获取新邮件；若反复失败，请联系管理员。
        </p>
        <div class="verify__actions">
          <AppButton variant="primary" @click="router.push('/login')">去注册 / 登录</AppButton>
          <AppButton variant="secondary" @click="router.push('/')">回到题库</AppButton>
        </div>
      </template>
    </div>
  </main>
</template>

<style scoped>
.verify {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--space-4);
  padding: var(--space-10) var(--space-5);
}

.verify__mark {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 40px;
  font-weight: 700;
  color: var(--verdict-ac-text);
  background: var(--verdict-ac-bg);
  border: 1px solid var(--verdict-ac-text);
}

.verify__mark--fail {
  color: var(--verdict-wa-text);
  background: var(--verdict-wa-bg);
  border-color: var(--verdict-wa-text);
}

.verify__lead {
  margin: 0;
  color: var(--text-secondary);
  max-width: 46ch;
}

.verify__actions {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
  justify-content: center;
}
</style>
