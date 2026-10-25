<script setup>
/**
 * 配置自检面板（挂 /about）：把「手动填写的变量」逐项做成可视化检查。
 * 绿=就绪，红=缺配置（附配置命令），灰=未登录/未探测。
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase, authMode } from '../api/supabase.js'
import { effectiveAuthMode, isLoggedIn, accessToken } from '../composables/useAuth.js'
import { probeConfig } from '../api/asyncSubmit.js'
import AppButton from '../components/AppButton.vue'

const router = useRouter()
const probing = ref(false)
const probeResult = ref(null)
const probeError = ref('')
const isReviewer = ref(null)

const items = computed(() => [
  {
    key: 'supabase',
    name: '前端 Supabase 配置（GitHub Secrets）',
    detail: 'VITE_SUPABASE_URL + VITE_SUPABASE_PUBLISHABLE_KEY',
    state: authMode ? 'ok' : 'bad'
  },
  {
    key: 'login',
    name: '登录状态',
    detail: '邮箱或 GitHub OAuth 登录后可用云功能',
    state: isLoggedIn.value ? 'ok' : 'bad'
  },
  {
    key: 'func',
    name: 'judge / admin-review 函数',
    detail: 'supabase functions deploy judge admin-review',
    state: probeResult.value ? 'ok' : probeError.value ? 'bad' : 'idle'
  },
  {
    key: 'uapi',
    name: 'UAPI 执行器（样例实跑）',
    detail: 'supabase secrets set UAPI_ACCESS_TOKEN=…',
    state: probeResult.value ? (probeResult.value.uapi_configured ? 'ok' : 'bad') : 'idle'
  },
  {
    key: 'ai',
    name: 'AI 评分（如 DeepSeek）',
    detail: 'supabase secrets set AI_API_KEY=… AI_API_URL=… AI_MODEL=…',
    state: probeResult.value ? (probeResult.value.ai_configured ? 'ok' : 'bad') : 'idle'
  },
  {
    key: 'secret',
    name: '服务端 Secret Key',
    detail: 'supabase secrets set SUPABASE_SECRET_KEY=sb_secret_…',
    state: probeResult.value ? (probeResult.value.secret_configured ? 'ok' : 'bad') : 'idle'
  },
  {
    key: 'admin',
    name: '人工复核管理员',
    detail: 'insert into public.reviewers (id) values (\'<你的 UID>\');（/admin-review 页可复制现成 SQL）',
    state: isReviewer.value === null ? 'idle' : isReviewer.value ? 'ok' : 'bad'
  }
])

async function runProbe() {
  if (probing.value) return
  probing.value = true
  probeError.value = ''
  probeResult.value = null
  try {
    const res = await probeConfig(accessToken())
    probeResult.value = res
  } catch (e) {
    probeError.value =
      e && e.message && /必须提供显式测试样例|source_code 与 files/.test(e.message)
        ? 'judge 函数为旧版（probe 被参数校验拦截）：请重新部署 supabase/functions/judge（新代码已修复）'
        : (e && e.message) || '探测失败'
  } finally {
    probing.value = false
    // 顺带检测管理员身份
    try {
      const { data: me } = await supabase.auth.getUser()
      const uid = me && me.user && me.user.id
      if (uid) {
        const { data: row } = await supabase.from('reviewers').select('id').eq('id', uid).maybeSingle()
        isReviewer.value = !!row
      }
    } catch {
      isReviewer.value = false
    }
  }
}

onMounted(() => {
  if (effectiveAuthMode.value && isLoggedIn.value) runProbe()
})
</script>

<template>
  <section class="cfg" aria-label="配置自检">
    <div class="cfg__bar">
      <h2 class="cfg__title">配置自检</h2>
      <AppButton variant="secondary" :loading="probing" :disabled="!isLoggedIn" @click="runProbe">
        {{ probing ? '探测中…' : '重新探测' }}
      </AppButton>
    </div>
    <p v-if="!authMode" class="caption">未配置 Supabase（本地模式）：云功能不可用属正常，本地判题不受影响。</p>
    <p v-else-if="!isLoggedIn" class="caption">
      登录后点「重新探测」，逐项检查云功能所需的密钥/管理员配置。
    </p>
    <p v-else-if="probeError" class="caption cfg__err">{{ probeError }}</p>

    <ul class="cfg__list">
      <li v-for="it in items" :key="it.key" class="cfg__row">
        <span class="cfg__dot" :class="`cfg__dot--${it.state}`" aria-hidden="true"></span>
        <span class="cfg__name">{{ it.name }}</span>
        <span class="cfg__state mono-data">
          {{ it.state === 'ok' ? '就绪' : it.state === 'bad' ? '缺配置' : '待探测' }}
        </span>
        <span class="cfg__detail caption">{{ it.detail }}</span>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.cfg {
  border: var(--border);
  background: var(--bg-surface);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.cfg__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.cfg__title {
  margin: 0;
  font-size: var(--text-h3);
}

.cfg__err {
  color: var(--danger-text);
  margin: 0;
}

.cfg__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.cfg__row {
  display: grid;
  grid-template-columns: 12px minmax(160px, 1fr) 64px minmax(200px, 2fr);
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-2) 0;
  border-bottom: var(--border);
}

.cfg__row:last-child {
  border-bottom: none;
}

.cfg__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--text-disabled);
}

.cfg__dot--ok {
  background: var(--verdict-ac-text);
}

.cfg__dot--bad {
  background: var(--verdict-wa-text);
}

.cfg__state {
  font-size: var(--text-micro);
  color: var(--text-secondary);
}

.cfg__detail {
  color: var(--text-muted);
  overflow-wrap: anywhere;
}

@media (max-width: 640px) {
  .cfg__row {
    grid-template-columns: 12px 1fr auto;
  }

  .cfg__detail {
    grid-column: 2 / -1;
  }
}
</style>
