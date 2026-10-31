/**
 * 语法高亮（highlight.js 精简内核：只注册题库/文档用到的语言，控制体积）。
 * 输出 token span（class="hljs-*"），配色见 styles/hljs.css（终端色板）。
 */
import hljs from 'highlight.js/lib/core'
import cpp from 'highlight.js/lib/languages/cpp'
import makefile from 'highlight.js/lib/languages/makefile'
import bash from 'highlight.js/lib/languages/bash'
import json from 'highlight.js/lib/languages/json'
import python from 'highlight.js/lib/languages/python'

hljs.registerLanguage('cpp', cpp)
hljs.registerLanguage('c', cpp)
hljs.registerLanguage('cxx', cpp)
hljs.registerLanguage('cc', cpp)
hljs.registerLanguage('h', cpp)
hljs.registerLanguage('hpp', cpp)
hljs.registerLanguage('makefile', makefile)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('shell', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('json', json)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)

/** 文件名 → 高亮语言（提交回显 / 多文件编辑按扩展名归类） */
const EXT_LANG = {
  cpp: 'cpp',
  cc: 'cpp',
  cxx: 'cpp',
  c: 'c',
  h: 'cpp',
  hpp: 'cpp',
  makefile: 'makefile',
  mk: 'makefile',
  sh: 'bash',
  bash: 'bash',
  json: 'json',
  py: 'python',
  python: 'python'
}

/**
 * 按文件名推断语言（Makefile 无扩展名，按 basename 归 makefile）。
 * @param {string} name
 * @returns {string} '' = 无法判定（调用方回退纯文本）
 */
export function langFromFilename(name) {
  const base = String(name || '').split(/[\\/]/).pop() || ''
  if (/^makefile$/i.test(base) || /^gnumakefile$/i.test(base)) return 'makefile'
  const ext = base.includes('.') ? base.split('.').pop().toLowerCase() : ''
  return EXT_LANG[ext] || ''
}

/**
 * 高亮一段代码；语言未注册/为空时返回 ''（调用方回退纯文本转义）。
 * @param {string} code
 * @param {string} lang 围栏语言标记（cpp/makefile/bash/json/python…）
 * @returns {string} token HTML
 */
export function highlightCode(code, lang) {
  const language = String(lang || '').toLowerCase()
  if (!language || !hljs.getLanguage(language)) return ''
  try {
    return hljs.highlight(String(code), { language, ignoreIllegals: true }).value
  } catch {
    return ''
  }
}

export default hljs
