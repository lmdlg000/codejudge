/**
 * 逐页 TDK（content-plan 第 2 节逐字/模板）。
 * 本地工具站，仅保证标签页可读与信息架构一致。
 * 题库规模文案**从题库数据动态推导**（新增题目自动更新，不写死编号区间）。
 */
import problems from '../data/problems.json'

const SITE = 'CodeJudge'

/** P<n> 编号 → 「P1–P7」区间；非标准编号退化为 null（调用方走数量文案） */
function rangeLabel(items) {
  const ids = (items || []).map((p) => p.id).filter((id) => /^P\d+$/.test(id || ''))
  if (!ids.length || ids.length !== (items || []).length) return null
  const nums = ids.map((id) => Number(id.slice(1))).sort((a, b) => a - b)
  return nums[0] === nums[nums.length - 1] ? `P${nums[0]}` : `P${nums[0]}–P${nums[nums.length - 1]}`
}

/** 题库规模（构建期随 problems/ 自动更新） */
export const PROBLEM_COUNT = problems.length
export const PROBLEM_RANGE_LABEL = rangeLabel(problems) || `${PROBLEM_COUNT} 道`

const RANGE_TEXT = rangeLabel(problems) ? `${PROBLEM_RANGE_LABEL} 题库` : `${PROBLEM_COUNT} 道题题库`
const DESC_SCALE = rangeLabel(problems)
  ? `内置 ${PROBLEM_RANGE_LABEL} 共 ${PROBLEM_COUNT} 道 C++ 题`
  : `内置 ${PROBLEM_COUNT} 道 C++ 题`

/** 默认（首页） */
export const TDK_HOME = {
  title: `${SITE} 在线代码评测台 · ${RANGE_TEXT}`,
  description: `本地运行的在线代码评测台，${DESC_SCALE}。贴上代码提交后逐用例返回 AC/WA/TLE 等判定与得分，支持 ACM 与 OI 双模式，源码不离开本机。`
}

/**
 * @param {{title:string, description:string, robots?:string, keywords?:string}} tdk
 */
export function applyTdk(tdk) {
  if (tdk.title) document.title = tdk.title
  if (tdk.description) {
    let tag = document.querySelector('meta[name="description"]')
    if (!tag) {
      tag = document.createElement('meta')
      tag.setAttribute('name', 'description')
      document.head.appendChild(tag)
    }
    tag.setAttribute('content', tdk.description)
  }
  // robots：登录页 noindex（Δ1-8），其余页恢复 index 防泄漏
  let robots = document.querySelector('meta[name="robots"]')
  if (!robots) {
    robots = document.createElement('meta')
    robots.setAttribute('name', 'robots')
    document.head.appendChild(robots)
  }
  robots.setAttribute('content', tdk.robots || 'index, follow')
  if (tdk.keywords) {
    let kw = document.querySelector('meta[name="keywords"]')
    if (!kw) {
      kw = document.createElement('meta')
      kw.setAttribute('name', 'keywords')
      document.head.appendChild(kw)
    }
    kw.setAttribute('content', tdk.keywords)
  }
}

/** Δ1-8 登录页 TDK（noindex，不进 sitemap） */
export const TDK_LOGIN = {
  title: '登录 / 注册 · CodeJudge',
  description:
    '用邮箱或 GitHub 登录 CodeJudge，提交判题并云同步历史。未登录也可在本地匿名模式下使用。',
  keywords: '登录,注册,GitHub 登录,云同步',
  robots: 'noindex'
}

/**
 * 题目详情页 TDK（content-plan 页面 2 模板）。
 * 「一句题意」从 statement_md 首段截取。
 * @param {{id:string,title:string,statement_md:string,limits:{time_ms:number},contest_type:string,score:number}} p
 */
export function problemTdk(p) {
  const intent = firstSentence(p.statement_md)
  return {
    title: `${p.title} · 在线提交判题 | ${SITE}`,
    description: `${p.title}（${p.id}）题面与在线提交：${intent}。时限 ${p.limits.time_ms}ms，${p.contest_type === 'oi' ? 'OI' : 'ACM'} 模式，满分 ${p.score}。贴上 C++ 代码立即出逐用例判定与差异提示。`
  }
}

/** 从 markdown 取「题目背景」后第一段的一句话 */
function firstSentence(md) {
  if (!md) return '在线作答并提交判题'
  const lines = String(md).split(/\r?\n/)
  let inBody = false
  for (const line of lines) {
    const t = line.trim()
    if (/^##\s*题目背景/.test(t)) {
      inBody = true
      continue
    }
    if (inBody && /^##\s*/.test(t)) break
    if (inBody && t && !t.startsWith('#')) {
      const sent = t.split(/(?<=[。！？])/)[0]
      return (sent || t).replace(/`/g, '').slice(0, 60)
    }
  }
  return '在线作答并提交判题'
}

export const TDK_RESULT = {
  // {题名} 在使用处替换
  title: (name) => `判定结果 · ${name} | ${SITE}`,
  description:
    '查看本次提交的逐用例判定：耗时、权重、差异行号，以及 CE 编译输出与 RE 信号提示。得分横幅给出通过率与得分。'
}

export const TDK_HISTORY = {
  title: `提交历史 · 本地评测记录 | ${SITE}`,
  description:
    '本机每一次评测的时间、题目、判定与得分都在这里，可按题目筛选，点任意一行直达逐用例判定结果。'
}

export const TDK_ABOUT = {
  title: `使用说明 · 判定规则与本地运行 | ${SITE}`,
  description:
    '从安装命令到看懂七种判定：判题流水线、ACM 与 OI 计分区别、CE 编译输出与 RE 信号说明，一页讲完。'
}
