<script setup>
/**
 * 页面 2：题目详情 + 在线提交 `/problems/:pid`（核心转化动作发生页）。
 * 交互冻结：同步判题——点「提交判题」→ loading「判题中…（最长约 2 分钟）」
 * → POST /api/submissions 返回全量结果后 router.push('/submissions/'+sid)。
 * make 题（P6）强制多文件提交。
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownView from '../components/MarkdownView.vue'
import CodeEditor from '../components/CodeEditor.vue'
import FileListEditor from '../components/FileListEditor.vue'
import OneCompilerEditor from '../components/OneCompilerEditor.vue'
import CodeBlock from '../components/CodeBlock.vue'
import TagBar from '../components/TagBar.vue'
import ErrorBar from '../components/ErrorBar.vue'
import AlertBar from '../components/AlertBar.vue'
import EmptyState from '../components/EmptyState.vue'
import AppButton from '../components/AppButton.vue'
import AppTabs from '../components/AppTabs.vue'
import { useProblem } from '../composables/useProblems.js'
import * as api from '../api/client.js'
import { submitForReview, verifySamples } from '../api/asyncSubmit.js'
import { toApiError } from '../api/errors.js'
import {
  effectiveAuthMode,
  isLoggedIn,
  accessToken,
  rememberRedirect
} from '../composables/useAuth.js'
import { problemTdk, applyTdk } from '../utils/tdk.js'
import { modeShort } from '../utils/format.js'

const route = useRoute()
const router = useRouter()

const { problem, loading, error, load } = useProblem()

/** 编辑器内容（P0 预填 main 骨架） */
const SKELETON = `#include <bits/stdc++.h>
using namespace std;

int main() {
    // 在这里写你的代码
    return 0;
}
`
const code = ref(SKELETON)
const filename = ref('main.cpp')

/** 提交形态：single 单文件（原有能力）| multi 多文件上传（新增，make 题强制） */
const submitMode = ref('single')
/** @type {{name:string, content:string}[]} */
const multiFiles = ref([])

/** 计分模式覆盖：default（跟随题目默认）| acm | oi */
const modeChoice = ref('default')

const submitting = ref(false)
const submitError = ref(null)

/** supabase 模式未登录拦截（Δ1-3）：置位后在主 CTA 下方出提示条 */
const loginRequired = ref(false)

/** 提交形态 tab（AppTabs 统一组件） */
const submitModeTabs = [
  { key: 'single', label: '单文件' },
  { key: 'multi', label: '多文件上传' }
]

function goLogin() {
  rememberRedirect(route.fullPath)
  router.push({ path: '/login', query: { redirect: route.fullPath } })
}

/** 示例代码（F9，P1 级，首发可做） */
const examples = ref([])
const examplesLoaded = ref(false)
const examplesError = ref(false)
const selectedExample = ref('')

const pid = computed(() => String(route.params.pid || ''))

/** make 多文件构建题（如 P6）：只开放多文件提交 */
const isMake = computed(() => {
  const b = problem.value && problem.value.build
  return !!(b && b.mode === 'make')
})

const canSubmit = computed(() => {
  if (submitting.value) return false
  if (submitMode.value === 'multi') {
    if (!(multiFiles.value.length > 0 && multiFiles.value.every((f) => f.content && f.content.trim().length > 0))) {
      return false
    }
  } else if (!code.value.trim()) {
    return false
  }
  // 双层校验·体验层：supabase 模式须显式样例全过才可提交
  return !needsSampleGate.value || samplesPassed.value
})

/** 显式样例自测（双层校验·体验层；后端 judge 仍会强制复验） */
const sampleStates = ref([]) // 每项：null=未运行 | {passed,status,expected,actual}
const verifying = ref(false)
const needsSampleGate = computed(() => effectiveAuthMode.value)
const samplesPassed = computed(
  () => sampleStates.value.length > 0 && sampleStates.value.every((s) => s && s.passed)
)

/** OneCompiler 嵌入式编辑器（supabase 模式代码测试面） */
const ocEditorRef = ref(null)

/** 样例测试次数（「测此样例」与「运行样例」累计）；≥10 次仍不过 → 解锁备用通道 */
const testAttempts = ref(0)
const FORCE_THRESHOLD = 10
const forceAvailable = computed(
  () => needsSampleGate.value && !samplesPassed.value && testAttempts.value >= FORCE_THRESHOLD
)

/** 在嵌入式编辑器内测单个样例：注入 stdin → 触发运行 → 比对输出；
 *  嵌入式未回传结果（如 Console/I-O 页签影响）→ 云端 dry_run 兜底。 */
async function testSampleInEditor(i) {
  const s = samples.value[i]
  if (!s || verifying.value) return
  verifying.value = true
  testAttempts.value += 1
  const states = [...sampleStates.value]
  states[i] = { running: true }
  sampleStates.value = states

  const norm = (x) => String(x ?? '').replace(/\r\n/g, '\n').replace(/[ \t]+$/gm, '').trim()
  let result = null
  let source = 'embed'
  // ① 嵌入式编辑器实跑（免费，OneCompiler 沙盒）
  if (ocEditorRef.value) {
    result = await ocEditorRef.value.runWithStdin(s.input)
  }
  // ② 兜底：云端 dry_run（UAPI 实跑，权威结果；带上 only_sample 供新版后端省调用）
  if (!result) {
    source = 'cloud'
    try {
      const payload = buildPayload()
      payload.only_sample = i
      const res = await verifySamples(payload, accessToken())
      const one = (res && res.samples && res.samples[i]) || null
      if (one) {
        result = { stdout: one.actual ?? '', status: one.status || '', stderr: '' }
      } else if (res && res.skipped) {
        result = { stdout: '', status: `执行器未配置（${res.skipped}）`, stderr: '' }
      }
    } catch (e) {
      submitError.value = toApiError(e)
    }
  }

  const next = [...sampleStates.value]
  if (!result) {
    next[i] = { passed: false, status: '未收到结果', expected: s.output, actual: '' }
  } else {
    const passed = norm(result.stdout) === norm(s.output)
    next[i] = {
      passed,
      status: passed ? (source === 'cloud' ? 'Accepted（云端实跑）' : 'Accepted') : result.status || 'Wrong Answer',
      expected: s.output,
      actual: result.stdout
    }
  }
  sampleStates.value = next
  verifying.value = false
}

/** 提交按钮禁用提示（按优先级取第一条未满足条件） */
const ctaHint = computed(() => {
  if (submitMode.value === 'multi') {
    if (!(multiFiles.value.length > 0 && multiFiles.value.every((f) => f.content && f.content.trim().length > 0))) {
      return '请先添加文件并保证每个文件都有内容。'
    }
  } else if (!code.value.trim()) {
    return '先写点代码再提交。空源码不会进入评测队列。'
  }
  if (needsSampleGate.value && !samplesPassed.value) {
    return '先「运行样例」并全部通过，再提交判题。'
  }
  return ''
})

/** 限制摘要构建串（P6 显示 make inspector） */
const contestTypeLabel = computed(() =>
  problem.value ? modeShort(problem.value.contest_type) : ''
)

/** 题面拆分：去掉样例节，样例用 samples[] 独立样式块渲染 */
const statementParts = computed(() => splitStatement(problem.value && problem.value.statement_md))

const samples = computed(() => (problem.value && problem.value.samples) || [])

/** 样例小标题：多样例时「样例输入 2」 */
function sampleTitle(kind, i) {
  return samples.value.length > 1 ? `${kind} ${i + 1}` : kind
}

/** 提交文件名：默认 build.default_filename 或 main.cpp */
function resolveFilename() {
  const b = problem.value && problem.value.build
  return (b && b.default_filename) || 'main.cpp'
}

function onUpload(text) {
  code.value = text
}

function fillExample() {
  const item = examples.value.find((e) => e.name === selectedExample.value)
  if (!item) return
  if (item.files && item.files.length) {
    // 多文件示例（如 P6_make/）：整套载入多文件提交区
    submitMode.value = 'multi'
    multiFiles.value = item.files.map((f) => ({ name: f.name, content: f.content }))
    return
  }
  // 单文件示例：切回单文件编辑器（make 题保持多文件模式，提示改用多文件示例）
  if (!isMake.value) {
    submitMode.value = 'single'
    code.value = item.content || ''
  } else {
    submitMode.value = 'multi'
    multiFiles.value = [{ name: 'main.cpp', content: item.content || '' }]
  }
}

/** 提交载荷（submit 与样例自测共用；supabase 模式带上 problem 元信息与样例） */
function buildPayload() {
  const payload = {
    problem_id: pid.value,
    language: 'cpp'
  }
  if (submitMode.value === 'multi') {
    payload.files = multiFiles.value.map((f) => ({ name: f.name, content: f.content }))
  } else {
    payload.source_code = code.value
    payload.filename = resolveFilename()
  }
  if (modeChoice.value === 'acm' || modeChoice.value === 'oi') {
    payload.mode = modeChoice.value
  }
  if (effectiveAuthMode.value) {
    const p = problem.value || {}
    payload.problem = {
      title: p.title || '',
      statement_md: p.statement_md || '',
      contest_type: p.contest_type || 'oi',
      limits: p.limits || { time_ms: 1000, memory_mb: 256 },
      build_mode: (p.build && p.build.mode) || 'g++',
      // 显式样例随提交上行：UAPI 前置校验入参 + AI 评判对照
      samples: p.samples || []
    }
  }
  return payload
}

/** 显式样例自测（dry_run，不落库）：逐样例跑 UAPI，回填通过状态 */
async function runSamplesNow() {
  if (verifying.value) return
  if (effectiveAuthMode.value && !isLoggedIn.value) {
    loginRequired.value = true
    rememberRedirect(route.fullPath)
    return
  }
  verifying.value = true
  submitError.value = null
  testAttempts.value += 1
  sampleStates.value = (problem.value?.samples || []).map(() => null)
  try {
    const res = await verifySamples(buildPayload(), accessToken())
    const list = (res && res.samples) || []
    sampleStates.value = list.map((s) => ({
      passed: !!s.passed,
      status: s.status || '',
      expected: s.expected ?? '',
      actual: s.actual ?? ''
    }))
  } catch (e) {
    submitError.value = toApiError(e)
  } finally {
    verifying.value = false
  }
}

async function submit(force = false) {
  const isForced = force === true
  if (submitting.value) return
  const codeOk =
    submitMode.value === 'multi'
      ? multiFiles.value.length > 0 && multiFiles.value.every((f) => f.content && f.content.trim().length > 0)
      : !!code.value.trim()
  if (!codeOk) return
  if (isForced) {
    // 备用通道：仅在测试 ≥10 次仍不过时可用（forceAvailable）
    if (!forceAvailable.value) return
  } else if (!canSubmit.value) {
    return
  }

  // supabase 模式「登录后判题」前置拦截（13.5：服务端 401 仅兜底）
  if (effectiveAuthMode.value && !isLoggedIn.value) {
    loginRequired.value = true
    // 保留编辑器内容：先落 sessionStorage，回跳后 init() 自动恢复
    try {
      sessionStorage.setItem(
        `codejudge-submit-${pid.value}`,
        JSON.stringify({ mode: submitMode.value, code: code.value, files: multiFiles.value })
      )
    } catch {
      /* ignore */
    }
    rememberRedirect(route.fullPath)
    return
  }
  loginRequired.value = false

  submitting.value = true
  submitError.value = null
  try {
    const payload = buildPayload()
    if (isForced) payload.force_submit = true

    // 保留本次源码：结果页「返回题目改代码」恢复用
    try {
      sessionStorage.setItem(
        `codejudge-submit-${pid.value}`,
        JSON.stringify({ mode: submitMode.value, code: code.value, files: multiFiles.value })
      )
    } catch {
      /* ignore */
    }

    let resultId = ''
    if (effectiveAuthMode.value) {
      // UAPI 异步流：前置样例校验通过后秒回执，AI 评分后台进行，Realtime 推送状态
      const receipt = await submitForReview(payload, accessToken())
      resultId = receipt.submissionId
    } else {
      // local 模式：同步判题（FastAPI），行为不变
      const result = await api.createSubmission(payload, null)
      resultId = result.submission_id
      try {
        sessionStorage.setItem(
          `codejudge-mode-${resultId}`,
          JSON.stringify({
            mode: result.mode,
            defaultMode: problem.value ? problem.value.contest_type : ''
          })
        )
        sessionStorage.removeItem(`codejudge-auth-${resultId}`)
      } catch {
        /* sessionStorage 不可用时静默 */
      }
    }
    router.push(`/submissions/${resultId}`)
  } catch (e) {
    submitError.value = toApiError(e)
  } finally {
    submitting.value = false
  }
}

async function loadExamples() {
  examplesLoaded.value = false
  examplesError.value = false
  examples.value = []
  selectedExample.value = ''
  try {
    const data = await api.getExamples(pid.value)
    examples.value = (data && data.items) || []
  } catch {
    // 404 / 400 / 网络失败均降级为「本题暂无示例代码。」
    examplesError.value = true
    examples.value = []
  } finally {
    examplesLoaded.value = true
  }
}

/**
 * 题面拆分：移除「## 样例输入/输出」各节，返回 { pre, post }。
 * 样例由 samples[] 以 CodeBlock 独立渲染（content-plan 区块 1）。
 */
function splitStatement(md) {
  if (!md) return { pre: '', post: '' }
  const lines = String(md).split(/\r?\n/)
  const pre = []
  const post = []
  let seenSample = false
  let skipping = false
  for (const line of lines) {
    const t = line.trim()
    if (/^##\s*样例(输入|输出)/.test(t)) {
      seenSample = true
      skipping = true
      continue
    }
    if (skipping) {
      if (/^##\s+/.test(t)) {
        skipping = false
        // 该标题属于样例之后的内容
      } else {
        continue
      }
    }
    ;(seenSample ? post : pre).push(line)
  }
  return { pre: pre.join('\n'), post: post.join('\n') }
}

async function init() {
  await load(pid.value)
  if (problem.value) {
    applyTdk(problemTdk(problem.value))
    filename.value = resolveFilename()
    // make 题强制多文件；g++ 题默认单文件
    submitMode.value = isMake.value ? 'multi' : 'single'
    // 恢复上次源码（结果页「返回题目改代码」）
    try {
      const saved = sessionStorage.getItem(`codejudge-submit-${pid.value}`)
      if (saved) {
        const prev = JSON.parse(saved)
        if (prev.mode === 'multi' && Array.isArray(prev.files) && prev.files.length) {
          submitMode.value = 'multi'
          multiFiles.value = prev.files
        } else if (typeof prev.code === 'string' && prev.code && !isMake.value) {
          code.value = prev.code
        }
      }
    } catch {
      /* ignore */
    }
  }
  loadExamples()
}

onMounted(init)
watch(() => route.params.pid, () => {
  if (route.name === 'problem-detail') {
    code.value = SKELETON
    multiFiles.value = []
    submitMode.value = 'single'
    modeChoice.value = 'default'
    submitError.value = null
    init()
  }
})

function onErrAction() {
  /* ErrorBar 内部已处理路由 */
}
</script>

<template>
  <main class="page">
    <div class="page__main container container--wide">
      <!-- 加载中 -->
      <p v-if="loading" class="caption" aria-live="polite">题目加载中…</p>

      <!-- 加载失败 -->
      <template v-else-if="error">
        <EmptyState
          v-if="error.code === 'PROBLEM_NOT_FOUND'"
          illustration="puzzle"
          illustration-title="题目数据缺失示意图"
          text="题目数据没读出来：检查 problems/<id>/problem.json 与 tests/ 目录是否完整（每个 .in 必须有同名 .out）。"
          action-label="回到题目列表"
          @action="router.push('/')"
        />
        <ErrorBar v-else :error="error" @action="onErrAction" />
      </template>

      <template v-else-if="problem">
        <div class="detail">
          <!-- ===== 左栏：面包屑 + H1 + 题面 ===== -->
          <div class="detail__left">
            <nav class="crumb" aria-label="面包屑">
              <router-link to="/">题目列表</router-link>
              <span class="crumb__sep" aria-hidden="true">/</span>
              <span class="mono-data">{{ problem.id }}</span>
            </nav>

            <h1>{{ problem.id }} {{ problem.title }}</h1>

            <!-- 题面（Markdown 渲染，样例节已拆出） -->
            <div class="detail__statement">
              <MarkdownView :source="statementParts.pre" />
            </div>

            <!-- 样例块（独立样式 + 复制样例） -->
            <section v-if="samples.length" class="samples" aria-label="样例">
              <figure
                v-for="(s, i) in samples"
                :key="i"
                class="samples__pair"
              >
                <h3 class="samples__title">{{ sampleTitle('样例输入', i) }}</h3>
                <CodeBlock :label="sampleTitle('样例输入', i)" copy-label="复制样例" :code="s.input" />
                <h3 class="samples__title">{{ sampleTitle('样例输出', i) }}</h3>
                <CodeBlock :label="sampleTitle('样例输出', i)" copy-label="复制样例" :code="s.output" />
              </figure>
            </section>

            <!-- 数据范围等样例之后的题面 -->
            <div v-if="statementParts.post.trim()" class="detail__statement detail__post">
              <MarkdownView :source="statementParts.post" :strip-h1="false" />
            </div>
          </div>

          <!-- ===== 右栏：限制摘要 + 编辑提交区 ===== -->
          <aside class="detail__right" aria-label="代码提交">
            <TagBar :problem="problem" />

            <!-- 语言说明行（固定） -->
            <p class="lang-line caption">
              语言：<span class="inline-code">C++17（g++ -O2）</span>
            </p>

            <!-- 提交错误提示条（编辑区上方） -->
            <ErrorBar
              v-if="submitError"
              :error="submitError"
              class="detail__error"
            />

            <!-- make 题提示（多文件构建） -->
            <AlertBar
              v-if="isMake"
              tone="info"
              title="本题为多文件 make 构建"
              message="请在下方多文件模式提交 Makefile 与全部源文件（如 Makefile + inspector.cpp + util.h），判题时执行 make <target> 构建。"
            />

            <!-- 提交形态切换（g++ 题：单文件 / 多文件；make 题强制多文件）—— AppTabs 统一组件 -->
            <AppTabs
              v-if="!isMake"
              v-model="submitMode"
              :tabs="submitModeTabs"
              aria-label="提交形态"
            />

            <!-- 编辑区 -->
            <div class="submit-area">
              <FileListEditor
                v-if="submitMode === 'multi'"
                v-model="multiFiles"
                min-height="300px"
              />
              <!-- supabase 模式：OneCompiler 嵌入式编辑器（写码 + 样例测试面） -->
              <OneCompilerEditor
                v-else-if="needsSampleGate"
                ref="ocEditorRef"
                v-model="code"
                height="520px"
              />
              <CodeEditor
                v-else
                v-model="code"
                :filename="filename"
                min-height="420px"
                @upload="onUpload"
              />

              <!-- 计分模式覆盖 -->
              <fieldset class="mode">
                <legend class="mode__legend caption">计分模式</legend>
                <label class="mode__opt">
                  <input v-model="modeChoice" type="radio" name="mode" value="default" />
                  <span>跟随题目默认（{{ contestTypeLabel }}）</span>
                </label>
                <label class="mode__opt">
                  <input v-model="modeChoice" type="radio" name="mode" value="acm" />
                  <span>ACM</span>
                </label>
                <label class="mode__opt">
                  <input v-model="modeChoice" type="radio" name="mode" value="oi" />
                  <span>OI</span>
                </label>
                <p class="mode__hint caption">
                  ACM：全部用例对才记满分，否则 0 分。OI：按通过用例的权重折算得分。
                </p>
              </fieldset>

              <!-- 示例代码一键填入（F9） -->
              <div class="examples">
                <label class="examples__label caption" for="example-select">示例代码：选择后一键填入</label>
                <div class="examples__row">
                  <select
                    id="example-select"
                    v-model="selectedExample"
                    class="examples__select"
                    :disabled="!examples.length"
                  >
                    <option v-if="!examples.length" value="" disabled>本题暂无示例代码。</option>
                    <option v-else value="" disabled>请选择示例</option>
                    <option v-for="e in examples" :key="e.name" :value="e.name">
                      {{ e.name }}（预期 {{ e.expect }}）
                    </option>
                  </select>
                  <AppButton
                    variant="secondary"
                    :disabled="!selectedExample"
                    @click="fillExample"
                  >填入编辑器</AppButton>
                </div>
                <p v-if="examplesLoaded && !examples.length" class="caption examples__empty">
                  本题暂无示例代码。
                </p>
                <p v-else class="caption examples__hint">
                  想看七种判定长什么样？选一个演示提交填入编辑器直接判。
                </p>
              </div>

              <!-- 显式样例自测（双层校验·体验层）：全部通过才启用提交 -->
              <div v-if="needsSampleGate && samples.length" class="sample-gate">
                <div class="sample-gate__bar">
                  <span class="caption sample-gate__title">显式样例自测（全部通过后可提交）</span>
                  <AppButton
                    variant="secondary"
                    :loading="verifying"
                    :disabled="!canSubmit && !(submitMode === 'multi' ? multiFiles.length : code.trim())"
                    @click="runSamplesNow"
                  >{{ verifying ? '样例运行中…' : '运行样例' }}</AppButton>
                </div>
                <ul class="sample-gate__list" aria-live="polite">
                  <li
                    v-for="(s, i) in samples"
                    :key="i"
                    class="sample-gate__item"
                  >
                    <span class="mono-data sample-gate__name">样例 {{ i + 1 }}</span>
                    <span
                      class="sample-gate__state mono-data"
                      :class="{
                        'sample-gate__state--run': sampleStates[i] && sampleStates[i].running,
                        'sample-gate__state--pass': sampleStates[i] && !sampleStates[i].running && sampleStates[i].passed,
                        'sample-gate__state--fail': sampleStates[i] && !sampleStates[i].running && !sampleStates[i].passed
                      }"
                    >
                      {{ !sampleStates[i] ? '待运行' : sampleStates[i].running ? '运行中…' : (sampleStates[i].passed ? '通过' : `失败（${sampleStates[i].status}）`) }}
                    </span>
                    <button
                      v-if="needsSampleGate && submitMode !== 'multi'"
                      type="button"
                      class="sample-gate__test"
                      :disabled="verifying"
                      @click="testSampleInEditor(i)"
                    >[ 测此样例 ]</button>
                  </li>
                </ul>
                <p v-if="samplesPassed" class="caption sample-gate__ok">样例全部通过，可以提交。</p>
                <p v-else-if="needsSampleGate" class="caption">
                  先「运行样例」并全部通过，再提交判题。
                  <template v-if="testAttempts > 0">
                    已测试 {{ testAttempts }} 次{{ testAttempts < FORCE_THRESHOLD ? `（满 ${FORCE_THRESHOLD} 次可走备用通道）` : '' }}。
                  </template>
                </p>
                <!-- 备用通道：测试 ≥10 次仍不过 → AI 判分 + 强制人工复核 -->
                <div v-if="forceAvailable" class="sample-gate__force">
                  <p class="caption">
                    已测试 {{ testAttempts }} 次仍未全部通过。可走备用通道提交——结果由 AI 参考评分并**强制转人工复核**，最终以人工裁决为准。
                  </p>
                  <AppButton variant="secondary" :loading="submitting" @click="submit(true)">
                    备用通道提交（转人工复核）
                  </AppButton>
                </div>
              </div>

              <!-- 主 CTA -->
              <div class="cta">
                <AppButton
                  variant="primary"
                  block
                  :loading="submitting"
                  :disabled="!canSubmit"
                  :title="canSubmit ? '' : ctaHint"
                  @click="submit(false)"
                >{{ submitting ? '判题中…（最长约 2 分钟）' : '提交判题' }}</AppButton>
                <p v-if="!canSubmit && !submitting" class="caption cta__hint">
                  {{ ctaHint }}
                </p>
              </div>

              <!-- supabase 模式未登录拦截条（主 CTA 正下方，Δ2-5） -->
              <AlertBar
                v-if="loginRequired"
                tone="info"
                message="登录后可提交判题并云同步历史。"
                action-label="去登录"
                action-key="goto-login"
                @action="goLogin"
              />
            </div>
          </aside>
        </div>
      </template>
    </div>
  </main>
</template>

<style scoped>
.detail {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: var(--space-8);
  align-items: start;
}

.detail__left {
  min-width: 0;
}

.detail__right {
  min-width: 0;
  position: sticky;
  top: calc(var(--header-h) + var(--space-4));
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.crumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-caption);
  color: var(--text-muted);
  margin-bottom: var(--space-3);
}

.crumb a {
  color: var(--text-muted);
}

.crumb a:hover {
  color: var(--primary);
}

.crumb__sep {
  color: var(--text-disabled);
}

.detail__statement {
  margin-top: var(--space-6);
}

.detail__post {
  margin-top: var(--space-6);
}

.samples {
  margin-top: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.samples__pair {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.samples__title {
  margin: 0;
  font-size: var(--text-h3);
}

.lang-line {
  margin: 0;
  color: var(--text-secondary);
}

.detail__error {
  margin-bottom: 0;
}

.submit-area {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.mode {
  border: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-4);
  align-items: center;
}

.mode__legend {
  padding: 0;
  margin-bottom: var(--space-2);
  color: var(--text-secondary);
  font-weight: 600;
}

.mode__opt {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-body);
  cursor: pointer;
  min-height: 44px;
}

.mode__opt input {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
}

.mode__hint {
  flex-basis: 100%;
  color: var(--text-muted);
}

.examples {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.examples__label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.examples__row {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.examples__select {
  flex: 1;
  min-width: 200px;
  height: var(--control-h);
  padding: 0 var(--space-3);
  border: var(--border-strong);
  border-radius: var(--radius);
  background: var(--bg-surface);
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
}

.examples__select:hover:not(:disabled) {
  border-color: var(--text-muted);
}

.examples__select:disabled {
  color: var(--text-disabled);
  cursor: not-allowed;
}

.examples__hint,
.examples__empty {
  color: var(--text-muted);
}

.cta {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

/* 显式样例自测（双层校验·体验层） */
.sample-gate {
  border: var(--border);
  background: var(--bg-surface);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.sample-gate__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.sample-gate__title {
  font-weight: 600;
  color: var(--text-secondary);
}

.sample-gate__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sample-gate__item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-caption);
}

.sample-gate__name {
  color: var(--text-secondary);
  min-width: 56px;
}

.sample-gate__state {
  color: var(--text-muted);
}

.sample-gate__state--pass {
  color: var(--verdict-ac-text);
}

.sample-gate__state--fail {
  color: var(--verdict-wa-text);
}

.sample-gate__state--run {
  color: var(--info-text);
}

.sample-gate__ok {
  color: var(--verdict-ac-text);
  margin: 0;
}

.sample-gate__test {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: var(--text-micro);
  color: var(--code-accent);
  background: transparent;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  padding: 2px 8px;
  cursor: pointer;
  min-height: 28px;
}

.sample-gate__test:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
}

.sample-gate__test:disabled {
  color: var(--text-disabled);
  cursor: not-allowed;
}

.sample-gate__force {
  border: 1px solid var(--warning-border);
  background: var(--warning-bg);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  align-items: flex-start;
}

.sample-gate__force .caption {
  color: var(--warning-text);
  margin: 0;
}

.cta__hint {
  color: var(--text-muted);
}

.p6-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-3);
}

/* 1024–1279：6/6 双栏 */
@media (max-width: 1279px) {
  .detail {
    grid-template-columns: 1fr 1fr;
    gap: var(--space-6);
  }
}

/* <1024：单列 题面 → 标签栏 → 编辑区 */
@media (max-width: 1023px) {
  .detail {
    grid-template-columns: 1fr;
  }

  .detail__right {
    position: static;
    margin-top: var(--space-6);
  }
}
</style>
