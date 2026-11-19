/**
 * contenteditable 编辑区的「纯文本 ↔ DOM」统一工具。
 *
 * 关键背景：Chromium 对 contenteditable 执行 execCommand('insertText', text) 时，
 * 会把 text 里的 \n 转成 <br>，而 element.textContent 又会把 <br> 完全丢掉。
 * 结果：粘贴多行代码 → 高亮刷新读出 textContent → 换行全部消失，代码挤成一行。
 *
 * 这里统一做四件事：
 *   1. getEditableText()：把 <br> / 块级元素边界还原成 \n（读模型用这个，不用 textContent）；
 *   2. captureEditableState / rehighlightEditable：选区、滚动、焦点按同一套文本偏移保存恢复；
 *   3. insertPlainText()：以文本节点插入纯文本，\n 原样保留（white-space: pre 下正常显示换行）；
 *   4. 刷新高亮时仍保留折叠与非折叠选区，不夺焦。
 */

/** 浏览器在 contenteditable 里按 Enter 时可能生成的块级标签 */
const BLOCK_TAGS = new Set([
  'ADDRESS', 'ARTICLE', 'ASIDE', 'BLOCKQUOTE', 'DIV', 'DL', 'DT', 'DD',
  'FIELDSET', 'FIGCAPTION', 'FIGURE', 'FOOTER', 'FORM', 'H1', 'H2', 'H3',
  'H4', 'H5', 'H6', 'HEADER', 'HR', 'LI', 'MAIN', 'NAV', 'OL', 'P', 'PRE',
  'SECTION', 'TABLE', 'TR', 'UL'
])

function indexIn(parent, node) {
  return Array.prototype.indexOf.call(parent.childNodes, node)
}

/**
 * 序列化可编辑区域：返回纯文本，可选「文本偏移 → DOM 位置」映射。
 * 文本节点里的 \n 原样保留；<br> 与块级边界补 \n。
 */
function serialize(root, withMap = false) {
  let text = ''
  const map = withMap ? [] : null

  function pushChar(ch, node, offset) {
    text += ch
    if (map) map.push({ node, offset })
  }

  function lineBreak(node, offset) {
    if (text && !text.endsWith('\n')) pushChar('\n', node, offset)
  }

  function walk(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      const data = node.data || ''
      if (withMap) {
        for (let i = 0; i < data.length; i++) pushChar(data[i], node, i)
      } else {
        text += data
      }
      return
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return
    if (node.nodeName === 'BR') {
      const parent = node.parentNode
      lineBreak(parent, parent ? indexIn(parent, node) + 1 : 0)
      return
    }
    if (BLOCK_TAGS.has(node.nodeName)) lineBreak(node, 0)
    for (const child of Array.from(node.childNodes)) walk(child)
  }

  for (const child of Array.from(root.childNodes || [])) walk(child)
  // 末尾位置：text.length 对应的 DOM 落点
  if (map) map.push({ node: root, offset: root.childNodes.length })
  return { text, map }
}

/** 从可编辑区域读取纯文本（保留换行），替代 textContent */
export function getEditableText(root) {
  return root ? serialize(root).text : ''
}

/** DOM 位置 → 纯文本偏移（按与 getEditableText 相同的序列化规则） */
function offsetOf(root, node, offset) {
  if (!root || !node) return 0
  if (node === root && offset === 0) return 0
  try {
    const range = document.createRange()
    range.selectNodeContents(root)
    range.setEnd(node, offset)
    return serialize(range.cloneContents()).text.length
  } catch {
    return 0
  }
}

/** 纯文本偏移 → DOM 位置 */
function pointAt(root, target) {
  if (!root) return { node: root, offset: 0 }
  const { map } = serialize(root, true)
  if (!map || !map.length) return { node: root, offset: 0 }
  const i = Math.max(0, Math.min(target, map.length - 1))
  return map[i]
}

/** 记录编辑区当前状态（选区两端 + 滚动 + 是否聚焦） */
export function captureEditableState(root) {
  if (!root) return null
  const state = {
    hasRange: false,
    start: 0,
    end: 0,
    focused: document.activeElement === root,
    scrollTop: root.scrollTop,
    scrollLeft: root.scrollLeft
  }
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0) return state
  const range = sel.getRangeAt(0)
  if (!root.contains(range.startContainer) || !root.contains(range.endContainer)) return state
  state.hasRange = true
  state.start = offsetOf(root, range.startContainer, range.startOffset)
  state.end = offsetOf(root, range.endContainer, range.endOffset)
  return state
}

/** 用新 HTML 替换内容，并把选区、滚动位置原样还回去 */
export function rehighlightEditable(root, html, state) {
  if (!root) return
  const saved = state || captureEditableState(root)
  root.innerHTML = html || ''
  if (!saved) return

  root.scrollTop = saved.scrollTop
  root.scrollLeft = saved.scrollLeft
  if (!saved.hasRange) return

  // 先夺回焦点再落选区：部分浏览器 focus() 会把光标重置到开头
  if (saved.focused && document.activeElement !== root) {
    root.focus({ preventScroll: true })
  }
  const start = pointAt(root, saved.start)
  const end = pointAt(root, saved.end)
  const range = document.createRange()
  range.setStart(start.node, start.offset)
  range.setEnd(end.node, end.offset)
  const sel = window.getSelection()
  if (sel) {
    sel.removeAllRanges()
    sel.addRange(range)
  }
}

/**
 * 在选区处插入纯文本。不能用 execCommand('insertText')：它会把 \n 变成 <br>，
 * 后续 textContent 读取就把换行丢光了。文本节点在 white-space: pre 下正常换行。
 */
export function insertPlainText(root, text) {
  if (!root || !window.getSelection) return
  const sel = window.getSelection()
  if (!sel || !sel.rangeCount) return
  const range = sel.getRangeAt(0)
  if (!root.contains(range.startContainer) || !root.contains(range.endContainer)) return
  const value = String(text ?? '').replace(/\r\n?/g, '\n')
  if (!value) return
  range.deleteContents()
  const node = document.createTextNode(value)
  range.insertNode(node)
  const after = document.createRange()
  after.setStartAfter(node)
  after.collapse(true)
  sel.removeAllRanges()
  sel.addRange(after)
}
