// scripts/build-problem-data.mjs —— 题库静态打包（frontend/src/data/problems.json）
// 用途：GitHub Pages 等无 FastAPI 场景下前端仍能拿到题面/样例/限制（AI 评分入参也来自这里）。
// 由 frontend/package.json 的 prebuild/predev 钩子调用（cwd=frontend）。
// 样例抽取规则与 core/importer.py 同源：## 样例输入( \d+)? / ## 样例输出( \d+)? + fenced code block。
import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync, statSync } from 'node:fs'
import { join, dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const root = resolve(here, '..')
const problemsDir = join(root, 'problems')
const outFile = join(root, 'frontend', 'src', 'data', 'problems.json')

function extractSamples(md) {
  const lines = String(md).split(/\r?\n/)
  const inputs = []
  const outputs = []
  let target = null
  let inFence = false
  let buf = []
  for (const line of lines) {
    const t = line.trim()
    if (/^##\s*样例(输入|输出)/.test(t)) {
      target = t.includes('输出') ? outputs : inputs
      continue
    }
    if (target && t.startsWith('```')) {
      if (inFence) {
        target.push(buf.join('\n'))
        buf = []
        inFence = false
      } else {
        inFence = true
      }
      continue
    }
    if (inFence) buf.push(line)
  }
  const n = Math.min(inputs.length, outputs.length)
  const samples = []
  for (let i = 0; i < n; i++) samples.push({ input: inputs[i], output: outputs[i] })
  return samples
}

function buildModeOf(build) {
  return build && (build.target || build.command === 'make') ? 'make' : 'g++'
}

function defaultFilenameOf(build, mode) {
  if (mode === 'make') return null
  return (build && build.src) || 'main.cpp'
}

const items = []
// 题号数值排序：P<n> 按数字升序（P2 < P10），非标准 id 排最后（与 core.problem.problem_id_key 同口径）
function idOrder(a, b) {
  const ma = /^P(\d+)$/.exec(a)
  const mb = /^P(\d+)$/.exec(b)
  if (ma && mb) return Number(ma[1]) - Number(mb[1])
  if (ma) return -1
  if (mb) return 1
  return a.localeCompare(b)
}
if (existsSync(problemsDir)) {
  for (const name of readdirSync(problemsDir).sort(idOrder)) {
    const dir = join(problemsDir, name)
    const metaPath = join(dir, 'problem.json')
    const stmtPath = join(dir, 'statement.md')
    if (!statSync(dir).isDirectory() || !existsSync(metaPath) || !existsSync(stmtPath)) continue
    const meta = JSON.parse(readFileSync(metaPath, 'utf-8'))
    const statement = readFileSync(stmtPath, 'utf-8')
    const build = meta.build || {}
    const mode = buildModeOf(build)
    items.push({
      id: meta.id || name,
      title: meta.title || name,
      contest_type: meta.contest_type || 'oi',
      score: meta.score != null ? meta.score : 100,
      compare_mode: meta.compare_mode || 'trim',
      limits: {
        time_ms: (meta.limits && meta.limits.time_ms) || 1000,
        memory_mb: (meta.limits && meta.limits.memory_mb) || 256
      },
      build: {
        mode,
        command: build.command || (mode === 'make' ? 'make' : 'g++'),
        src: build.src || null,
        default_filename: defaultFilenameOf(build, mode)
      },
      topic: meta.topic || null,
      difficulty: meta.difficulty || null,
      statement_md: statement,
      samples: extractSamples(statement),
      test_count: null // 静态包不数用例；列表卡缺省不渲染该格
    })
  }
}

mkdirSync(dirname(outFile), { recursive: true })
writeFileSync(outFile, JSON.stringify(items, null, 2), 'utf-8')
console.log(`[build-problem-data] ${items.length} problems -> frontend/src/data/problems.json`)
