<script setup>
/**
 * 页面 5：关于 / 使用说明 `/about`（静态内容）。
 * 区块：使用流程三步 → 判定含义表(#verdicts) → ACM/OI 计分 → CLI(#cli)
 * → 判题流水线 → 用例从哪来 → 本地处理声明(#privacy) → 账号与云同步(#account) → 返回入口。
 * 文案逐字取 content-plan 页面 5 / 第 4 节 / Δ1-6。
 */
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import VerdictBadge from '../components/VerdictBadge.vue'
import CodeBlock from '../components/CodeBlock.vue'
import CollapsePanel from '../components/CollapsePanel.vue'
import PipelineDiagram from '../components/PipelineDiagram.vue'
import AppButton from '../components/AppButton.vue'
import AlertBar from '../components/AlertBar.vue'
import ConfigCheck from '../components/ConfigCheck.vue'
import { configMismatch } from '../composables/useAuth.js'
import { VERDICTS, verdictMeta } from '../utils/verdicts.js'
import { TDK_ABOUT, applyTdk } from '../utils/tdk.js'

const router = useRouter()

/** content-plan §7：/about 判定 FAQ 区块挂 FAQPage（7 条判定问答，问答取第 4 节文案） */
function injectFaqJsonLd() {
  const el = document.createElement('script')
  el.type = 'application/ld+json'
  el.id = 'faq-jsonld'
  el.textContent = JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: VERDICTS.map((code) => {
      const m = verdictMeta(code)
      return {
        '@type': 'Question',
        name: `「${code}」（${m.label}）是什么意思？`,
        acceptedAnswer: { '@type': 'Answer', text: m.help }
      }
    })
  })
  document.head.appendChild(el)
}

function removeFaqJsonLd() {
  const el = document.getElementById('faq-jsonld')
  if (el) el.remove()
}

onMounted(() => {
  applyTdk(TDK_ABOUT)
  injectFaqJsonLd()
})

onUnmounted(removeFaqJsonLd)

/** 判定表行（content-plan 第 4 节逐字） */
const verdictRows = [
  {
    code: 'AC',
    trigger: '逐字符相等（trim 模式去掉末尾空行）',
    message: '—（message 为空时统一显示破折号）'
  },
  {
    code: 'PE',
    trigger: 'token 相等但文本不等',
    message: '仅空白差异（PE）：内容相同但换行/空格不一致'
  },
  {
    code: 'WA',
    trigger: '首个不一致行',
    message: '第 i 行不一致：期望 \'…\'，实际 \'…\'；行数不一致时：行数不一致：期望 X 行，实际 Y 行'
  },
  {
    code: 'TLE',
    trigger: '墙钟 > 1.5× 时限 或 CPU 时间 > 时限',
    message: '超时（限时 Nms）'
  },
  {
    code: 'RE',
    trigger: 'exit_code < 0 且信号可翻译',
    message: '信号翻译短句（如 SIGSEGV 段错误（空指针/越界））'
  },
  {
    code: 'CE',
    trigger: '构建非 0 退出 / 构建超时 60s',
    message: '编译失败，展开查看编译器输出'
  },
  {
    code: 'SE',
    trigger: '基础设施异常（题目/用例缺失、缺 .out、报告写入失败等），对应 CLI 返回码 2 / status=failed',
    message: '评测器自身异常，本次提交未完成判定'
  }
]

const CLI_CMDS = `python judge.py list                 # 列出 P1–P6 与用例（权重/时限/备注）
python judge.py run P1 examples/P1_ac.cpp    # 评测单个提交
python judge.py import-samples exercise/P1-shipping.md   # 从题面抽取样例
python judge.py gen P1 --ref reference/P1.cpp            # 用参考实现刷新 .out`

const REDLINE = `禁止把用户路径直接拼进 shell=True；构建命令模板中的 {bin}/{src} 必须做路径白名单校验。`
</script>

<template>
  <main class="page">
    <div class="page__main container container--narrow">
      <h1>从跑起来到看懂每一种判定，一页讲完</h1>

      <!-- 配置自检：手动变量逐项可视化（云模式密钥/管理员/函数版本） -->
      <ConfigCheck class="section" />

      <!-- 区块 1：使用流程三步 -->
      <section class="section" aria-labelledby="steps-title">
        <h2 id="steps-title">使用流程三步</h2>
        <ol class="steps">
          <li class="steps__item">
            <span class="steps__num" aria-hidden="true">1</span>
            <div>
              <h3 class="steps__name">选题</h3>
              <p>在题目列表点卡片，进详情看题面、样例与限制摘要。</p>
            </div>
          </li>
          <li class="steps__item">
            <span class="steps__num" aria-hidden="true">2</span>
            <div>
              <h3 class="steps__name">写码并提交</h3>
              <p>在等宽编辑区写代码（已预填 main 骨架），点「提交判题」。</p>
            </div>
          </li>
          <li class="steps__item">
            <span class="steps__num" aria-hidden="true">3</span>
            <div>
              <h3 class="steps__name">看结果</h3>
              <p>得分横幅 + 逐用例表格，每行标注判定、耗时、权重与差异提示；不满意点「返回题目改代码」再来一发。</p>
            </div>
          </li>
        </ol>
      </section>

      <!-- 区块 2：判定含义表 -->
      <section id="verdicts" class="section" aria-labelledby="verdicts-title">
        <h2 id="verdicts-title">判定含义表</h2>
        <div class="vtable-wrap">
          <table class="vtable">
            <caption class="sr-only">七种判定的触发条件、用户可见提示与帮助文案</caption>
            <thead>
              <tr>
                <th scope="col">判定</th>
                <th scope="col">触发条件</th>
                <th scope="col">看到什么</th>
                <th scope="col">怎么修</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in verdictRows" :key="row.code">
                <td>
                  <VerdictBadge :verdict="row.code" />
                  <span class="vtable__label">{{ verdictMeta(row.code).label }}</span>
                </td>
                <td class="vtable__cell">{{ row.trigger }}</td>
                <td class="vtable__cell">{{ row.message }}</td>
                <td class="vtable__cell">
                  <CollapsePanel
                    open-label="看帮助"
                    close-label="收起帮助"
                    max-height="200px"
                  >
                    <p class="vtable__help">{{ verdictMeta(row.code).help }}</p>
                  </CollapsePanel>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 区块 3：ACM / OI 计分说明 -->
      <section class="section" aria-labelledby="score-title">
        <h2 id="score-title">ACM / OI 计分说明</h2>
        <div class="two-col">
          <div class="panel">
            <h3 class="panel__title">OI</h3>
            <p>通过哪个用例就拿哪个的权重分。得分 = Σ 通过权重 / Σ 总权重 × 满分。适合练题看进度。</p>
          </div>
          <div class="panel">
            <h3 class="panel__title">ACM</h3>
            <p>全部用例 AC 才记满分，否则记 0；表格里的加权部分得分（partial_score）只作参考。适合模拟赛。</p>
          </div>
        </div>
        <p class="section__note">提交时可覆盖题目默认模式（详情页「计分模式」单选）。</p>
        <p class="section__note">两种模式的得分横幅句式相同：<code class="inline-code">通过 4/4 · 通过率 100% · 得分 100/100</code>。</p>
      </section>

      <!-- 区块 4：CLI 常用命令 -->
      <section id="cli" class="section" aria-labelledby="cli-title">
        <h2 id="cli-title">CLI 常用命令</h2>
        <CodeBlock label="bash" copy-label="复制命令" :code="CLI_CMDS" />
        <p class="section__note">
          预期输出：控制台打印逐用例表格，末行输出得分横幅：<code class="inline-code">通过 4/4 · 通过率 100% · 得分 100/100</code>
        </p>
        <p class="section__note">返回码：<code class="inline-code">0</code> 全 AC；<code class="inline-code">1</code> 非 AC；<code class="inline-code">2</code> 基础设施错误。</p>
      </section>

      <!-- 区块 5：判题流水线 -->
      <section class="section" aria-labelledby="pipe-title">
        <h2 id="pipe-title">判题流水线</h2>
        <ol class="pipe-steps">
          <li><code class="inline-code">builder</code> 编译/构建 —— 失败则全用例标 CE，直接跳过后面步骤。</li>
          <li><code class="inline-code">runner</code> 限时执行 —— stdin 注入用例输入，墙钟超时 1.5× 时限或 CPU 超时即终止。</li>
          <li><code class="inline-code">comparator</code> 比对 —— 先逐字符，再 token，给出首个差异行号。</li>
          <li><code class="inline-code">scorer</code> 计分 —— ACM/OI 复用同一份逐用例结果，只在最后合成得分。</li>
        </ol>
        <PipelineDiagram class="section__diagram" />
      </section>

      <!-- 区块 6：用例从哪来 -->
      <section class="section" aria-labelledby="tests-title">
        <h2 id="tests-title">用例从哪来</h2>
        <ol class="paths">
          <li>
            <h3 class="paths__name">手放</h3>
            <p><code class="inline-code">problems/Px/tests/42.in</code> + <code class="inline-code">42.out</code>，可选 <code class="inline-code">42.json</code> 覆盖权重/时限。</p>
          </li>
          <li>
            <h3 class="paths__name">生成</h3>
            <p><code class="inline-code">python judge.py gen Px --ref reference/Px.cpp</code> 用参考实现刷新 <code class="inline-code">.out</code>。</p>
          </li>
          <li>
            <h3 class="paths__name">抽取</h3>
            <p><code class="inline-code">python judge.py import-samples exercise/Px-*.md</code> 从题面样例块写入 <code class="inline-code">.in/.out</code>。</p>
          </li>
        </ol>
        <p class="section__note">三条路径写入同一目录，下次 run 自动纳入。</p>
      </section>

      <!-- 区块 7：本地处理声明 -->
      <section id="privacy" class="section" aria-labelledby="privacy-title">
        <h2 id="privacy-title">本机判题、数据不出机</h2>
        <p>
          源码与判题全程在本机进程内流转，报告只写入本地 <code class="inline-code">reports/</code> 目录，不联网、不上传。本地模式用 setrlimit（CPU/内存/文件大小）+ 墙钟超时 + 输出上限（stdout/stderr 各 4MB）保护。本项目只许本机自用，绝不暴露公网；若日后对外部署，须在 runner 上加 cgroup v2 + seccomp + 独立低权用户（nsjail/isolate），不在本期范围内。
        </p>
        <p class="redline">
          <span class="redline__label">红线提醒</span>
          <code class="inline-code">{{ REDLINE }}</code>
        </p>
      </section>

      <!-- 区块：账号与云同步（Δ1-6，锚点 #account，插在本地处理声明之后、返回入口之前） -->
      <section id="account" class="section" aria-labelledby="account-title">
        <h2 id="account-title">账号与云同步</h2>

        <!-- 两端配置不一致提示（13.4 降级规则） -->
        <AlertBar
          v-if="configMismatch"
          tone="warning"
          message="前后端云配置不一致：前端已配置 Supabase，但后端未启用云端入库。当前按本地模式运行。"
          extra="请检查 backend/.env 的 SUPABASE_URL 与 SUPABASE_SECRET_KEY 后重启后端。"
        />

        <ol class="paths">
          <li>
            <h3 class="paths__name">注册与登录</h3>
            <p>邮箱 + 密码（至少 8 位）注册，或 GitHub 一键登录。登录后提交判题，历史入你的账号，换机登录即见。</p>
          </li>
          <li>
            <h3 class="paths__name">GitHub OAuth 说明</h3>
            <p>点「使用 GitHub 登录」跳转 GitHub 授权页，同意授权后自动回本站。首次使用即自动创建账号，不需要再填密码；GitHub 账号邮箱需完成验证，未验证的提示见 Δ1-7。</p>
          </li>
          <li>
            <h3 class="paths__name">数据归属</h3>
            <p>云端历史（时间、题目、判定、得分与报告明细）随账号走，按账号隔离，其他账号看不到你的记录。本机 <code class="inline-code">reports/</code> 目录始终保留每次判题的原始报告文件；删除账号即删除其云端历史。</p>
          </li>
          <li>
            <h3 class="paths__name">隐私声明更新（双模式表述）</h3>
            <p>本地模式（未配置 Supabase）：判题与历史都在本机，数据不出机。</p>
            <p>云模式（已登录）：判题仍在本机执行，源码不上传第三方；<strong>入库的只有判题历史</strong>（含提交源码回显，便于换机回看），存入 Supabase，按账号隔离。源码不用于训练、不对外共享。</p>
            <p>页脚声明行相应替换为：<code class="inline-code">本地模式数据不出机；云模式仅判题历史入你的账号。</code></p>
            <p>本地匿名历史与云端历史互不迁移：换机或清理浏览器后，本地匿名历史不可恢复；云端历史随账号保留。</p>
          </li>
        </ol>
      </section>

      <!-- 区块 8：返回入口 -->
      <div class="actions">
        <AppButton variant="primary" @click="router.push('/')">回题目列表做题</AppButton>
        <AppButton variant="secondary" @click="router.push('/problems/P1')">从 P1 运费计算开始</AppButton>
      </div>
    </div>
  </main>
</template>

<style scoped>
.section {
  margin-top: var(--section-gap);
}

.section__note {
  margin-top: var(--space-3);
  color: var(--text-secondary);
  font-size: var(--text-body);
  line-height: var(--lh-body);
}

.section__diagram {
  margin-top: var(--space-4);
}

/* 三步 */
.steps {
  list-style: none;
  margin: var(--space-4) 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.steps__item {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
}

.steps__num {
  flex: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--primary-bg);
  color: var(--primary);
  font-family: var(--font-mono);
  font-size: var(--text-mono-badge);
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
}

.steps__name {
  font-size: var(--text-h4);
  margin: 0 0 var(--space-1);
}

/* 判定表 */
.vtable-wrap {
  margin-top: var(--space-4);
  background: var(--bg-surface);
  border: var(--border);
  border-radius: var(--radius);
  overflow-x: auto;
}

.vtable {
  width: 100%;
  border-collapse: collapse;
  min-width: 720px;
}

.vtable th {
  height: var(--table-head-h);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-subtle);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-align: left;
  border-bottom: var(--border);
}

.vtable td {
  padding: var(--space-3);
  border-bottom: var(--border);
  vertical-align: top;
  font-size: var(--text-caption);
  line-height: var(--lh-caption);
  color: var(--text-secondary);
}

.vtable tbody tr:last-child td {
  border-bottom: none;
}

.vtable__label {
  display: block;
  margin-top: var(--space-1);
  font-size: var(--text-caption);
  color: var(--text-primary);
}

.vtable__cell {
  max-width: 220px;
}

.vtable__help {
  color: var(--text-secondary);
  font-size: var(--text-caption);
  line-height: var(--lh-caption);
}

/* 两栏对照 */
.two-col {
  margin-top: var(--space-4);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.panel {
  background: var(--bg-surface);
  border: var(--border);
  border-radius: var(--radius);
  padding: var(--space-5);
}

.panel__title {
  margin: 0 0 var(--space-2);
}

.panel p {
  color: var(--text-secondary);
  font-size: var(--text-body);
  line-height: var(--lh-body);
}

/* CLI / 路径 */
.pipe-steps,
.paths {
  margin: var(--space-4) 0 0;
  padding-left: 1.3em;
  color: var(--text-secondary);
  font-size: var(--text-body);
  line-height: var(--lh-body);
}

.pipe-steps li + li,
.paths li + li {
  margin-top: var(--space-2);
}

.paths__name {
  font-size: var(--text-h4);
  color: var(--text-primary);
  margin: var(--space-2) 0 var(--space-1);
}

/* 红线提醒 */
.redline {
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--danger-bg);
  border: var(--border);
  border-left: 3px solid var(--danger-text);
  border-radius: var(--radius);
}

.redline__label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--danger-text);
  margin-bottom: var(--space-2);
}

.redline .inline-code {
  background: var(--bg-surface);
  color: var(--danger-text);
  display: block;
  white-space: pre-wrap;
}

.actions {
  margin-top: var(--section-gap);
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

@media (max-width: 640px) {
  .two-col {
    grid-template-columns: 1fr;
  }
}
</style>
